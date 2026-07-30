import csv
import html
import io
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import folium
import requests
from folium.plugins import HeatMap

NSW_TILE_URL = (
    "https://maps.six.nsw.gov.au/arcgis/rest/services/"
    "public/NSW_Imagery/MapServer/tile/{z}/{y}/{x}"
)
WEATHER_STATIONS_URL = "https://swd.weatherflow.com/swd/rest/map/stations"
WEATHER_OBSERVATIONS_URL = (
    "https://swd.weatherflow.com/swd/rest/observations/location"
)
OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"
API_KEY = "6bff2f89-84ab-463c-886e-fc0f443da4cf"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
STATION_SEARCH_BUFFER = 0.5
DEFAULT_CENTRE = [-33.8688, 151.2093]
DEFAULT_ZOOM = 17
WEATHER_CACHE_TTL = timedelta(hours=1)
DEFAULT_MARKER_COLOR = "blue"
MARKERS_JSON_PATH = Path(__file__).with_name("markers.json")
MARKER_COLORS = {
    "blue": "Blue",
    "red": "Red",
    "green": "Green",
    "purple": "Purple",
    "orange": "Orange",
    "black": "Black",
}


def safe_popup_html(title, description):
    title = html.escape(title)
    description = html.escape(description).replace("\n", "<br>")
    if not description:
        return f"<strong>{title}</strong>"
    return (
        f"<div style='min-width:220px'><strong>{title}</strong>"
        f"<div style='margin-top:8px'>{description}</div></div>"
    )


def make_marker(*, title, description, color, latitude, longitude):
    return {
        "id": str(uuid4()),
        "title": title,
        "description": description,
        "color": color,
        "latitude": latitude,
        "longitude": longitude,
    }


def make_markers_from_csv(csv_text):
    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        return [], ["CSV must include a header row."]

    reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
    missing = {"title", "latitude", "longitude"} - set(reader.fieldnames)
    if missing:
        return [], [f"CSV is missing required column(s): {', '.join(sorted(missing))}."]

    markers, errors = [], []
    for row_number, row in enumerate(reader, start=2):
        title = (row.get("title") or "").strip()
        color = (row.get("color") or DEFAULT_MARKER_COLOR).strip().lower()
        if not title:
            errors.append(f"Row {row_number}: missing title.")
            continue
        if color not in MARKER_COLORS:
            color = DEFAULT_MARKER_COLOR
        try:
            latitude = float(row.get("latitude", ""))
            longitude = float(row.get("longitude", ""))
        except (TypeError, ValueError):
            errors.append(f"Row {row_number}: invalid latitude/longitude.")
            continue
        markers.append(
            make_marker(
                title=title,
                description=(row.get("description") or "").strip(),
                color=color,
                latitude=latitude,
                longitude=longitude,
            )
        )
    return markers, errors


def fetch_osrm_route(start_marker, end_marker):
    coordinates = (
        f"{start_marker['longitude']},{start_marker['latitude']};"
        f"{end_marker['longitude']},{end_marker['latitude']}"
    )
    try:
        response = requests.get(
            f"{OSRM_ROUTE_URL}/{coordinates}",
            params={"overview": "full", "geometries": "geojson", "steps": "false"},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
    except requests.Timeout as error:
        raise RuntimeError("OSRM request timed out.") from error
    except requests.HTTPError as error:
        raise RuntimeError(f"OSRM returned HTTP {response.status_code}.") from error
    except requests.RequestException as error:
        raise RuntimeError(f"Could not reach OSRM: {error}.") from error
    except ValueError as error:
        raise RuntimeError("OSRM returned invalid JSON.") from error

    routes = data.get("routes") or []
    if data.get("code") != "Ok" or not routes:
        raise RuntimeError(data.get("message") or "No route found.")

    route = routes[0]
    route_coordinates = (route.get("geometry") or {}).get("coordinates") or []
    if not route_coordinates:
        raise RuntimeError("OSRM returned a route without geometry.")
    return {
        "start_id": start_marker["id"],
        "end_id": end_marker["id"],
        "start_title": start_marker["title"],
        "end_title": end_marker["title"],
        "distance_m": float(route.get("distance", 0)),
        "duration_s": float(route.get("duration", 0)),
        "coordinates": [
            [latitude, longitude] for longitude, latitude in route_coordinates
        ],
    }


def clean_marker(marker):
    try:
        title = str(marker.get("title") or "").strip()
        latitude = float(marker.get("latitude", ""))
        longitude = float(marker.get("longitude", ""))
    except (TypeError, ValueError):
        return None
    if not title:
        return None

    color = marker.get("color", DEFAULT_MARKER_COLOR)
    clean = {
        "id": str(marker.get("id") or uuid4()),
        "title": title,
        "description": str(marker.get("description") or ""),
        "color": color if color in MARKER_COLORS else DEFAULT_MARKER_COLOR,
        "latitude": latitude,
        "longitude": longitude,
    }
    weather = marker.get("weather")
    if isinstance(weather, dict) and (
        weather.get("temperature") is not None or weather.get("humidity") is not None
    ):
        clean["weather"] = {
            "temperature": weather.get("temperature"),
            "humidity": weather.get("humidity"),
        }
    for key in (
        "weather_fetched_at",
        "weather_location_id",
        "weather_error",
        "weather_attempted_at",
    ):
        if marker.get(key):
            clean[key] = marker[key]
    return clean


def timestamp_is_fresh(value):
    if not value:
        return False
    try:
        timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - timestamp < WEATHER_CACHE_TTL


def has_fresh_weather(marker):
    return bool(marker.get("weather")) and timestamp_is_fresh(
        marker.get("weather_fetched_at")
    )


def needs_weather(marker):
    return not has_fresh_weather(marker) and not timestamp_is_fresh(
        marker.get("weather_attempted_at")
    )


def load_markers():
    if not MARKERS_JSON_PATH.exists():
        return []
    try:
        data = json.loads(MARKERS_JSON_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return [
        clean
        for item in data
        if isinstance(item, dict) and (clean := clean_marker(item)) is not None
    ]


def save_markers(markers):
    clean_markers = [
        clean for marker in markers if (clean := clean_marker(marker)) is not None
    ]
    MARKERS_JSON_PATH.write_text(
        json.dumps(clean_markers, indent=2), encoding="utf-8"
    )


def get_weather_location_id(latitude, longitude):
    response = requests.get(
        WEATHER_STATIONS_URL,
        params={
            "api_key": API_KEY,
            "lat_min": latitude - STATION_SEARCH_BUFFER,
            "lon_min": longitude - STATION_SEARCH_BUFFER,
            "lat_max": latitude + STATION_SEARCH_BUFFER,
            "lon_max": longitude + STATION_SEARCH_BUFFER,
        },
        headers=HEADERS,
        timeout=15,
    )
    response.raise_for_status()
    stations = [
        (station["id"], station["geometry"]["coordinates"])
        for station in response.json()["features"]
    ]
    if not stations:
        raise RuntimeError("No weather stations found near marker.")
    return min(
        stations,
        key=lambda station: math.hypot(
            station[1][1] - latitude, station[1][0] - longitude
        ),
    )[0]


def fetch_weather_summary(location_id):
    response = requests.get(
        WEATHER_OBSERVATIONS_URL,
        params={"api_key": API_KEY, "location_id": location_id},
        headers=HEADERS,
        timeout=15,
    )
    response.raise_for_status()
    weather = response.json()
    if (weather.get("status") or {}).get("status_code") != 0:
        raise RuntimeError("Weather API returned an unsuccessful response.")

    observation = weather.get("outdoor")
    if not isinstance(observation, dict):
        observations = weather.get("obs") or weather.get("observations") or []
        observation = observations[0] if observations else {}
    temperature = observation.get("air_temperature")
    humidity = observation.get("relative_humidity")
    if temperature is None and humidity is None:
        raise RuntimeError("Weather API returned no temperature or humidity.")
    return {"temperature": temperature, "humidity": humidity}


def load_weather_for_markers(markers, on_progress=None):
    pending = [marker for marker in markers if needs_weather(marker)]
    if on_progress:
        on_progress(0, len(pending))

    weather_cache = {
        marker["weather_location_id"]: (
            marker["weather"],
            marker["weather_fetched_at"],
        )
        for marker in markers
        if marker.get("weather_location_id") and has_fresh_weather(marker)
    }
    for index, marker in enumerate(pending, start=1):
        try:
            location_id = get_weather_location_id(
                marker["latitude"], marker["longitude"]
            )
            marker["weather_location_id"] = location_id
            if location_id not in weather_cache:
                weather_cache[location_id] = (
                    fetch_weather_summary(location_id),
                    datetime.now(timezone.utc).isoformat(),
                )
            marker["weather"], marker["weather_fetched_at"] = weather_cache[location_id]
            marker.pop("weather_error", None)
            marker.pop("weather_attempted_at", None)
        except Exception:
            marker.pop("weather", None)
            marker.pop("weather_fetched_at", None)
            marker["weather_error"] = "Could not load weather data."
            marker["weather_attempted_at"] = datetime.now(timezone.utc).isoformat()
        if on_progress:
            on_progress(index, len(pending))
    if pending:
        save_markers(markers)


def format_weather(marker):
    if needs_weather(marker):
        return "Loading..."
    weather = marker.get("weather")
    if not weather:
        return marker.get("weather_error", "Unavailable")
    values = []
    if weather.get("temperature") is not None:
        values.append(f"Temperature: {weather['temperature']} C")
    if weather.get("humidity") is not None:
        values.append(f"Humidity: {weather['humidity']}%")
    return "\n".join(values) or "Unavailable"


def build_aerial_map(markers=None, show_heatmap=False):
    aerial_map = folium.Map(
        location=DEFAULT_CENTRE,
        zoom_start=DEFAULT_ZOOM,
        tiles=None,
        control_scale=True,
        prefer_canvas=True,
    )
    folium.TileLayer(
        tiles=NSW_TILE_URL,
        name="High-res aerial (NSW only)",
        attr="© NSW Spatial Services",
        min_zoom=0,
        max_zoom=23,
        max_native_zoom=23,
        overlay=False,
        control=True,
        show=True,
    ).add_to(aerial_map)
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="OpenStreetMap",
        overlay=False,
        control=True,
        show=False,
    ).add_to(aerial_map)
    if show_heatmap and markers:
        HeatMap(
            [[marker["latitude"], marker["longitude"], 1] for marker in markers],
            name="Marker density",
            radius=35,
            blur=25,
            min_opacity=0.25,
            max_zoom=18,
            gradient={
                0.2: "blue",
                0.4: "lime",
                0.6: "yellow",
                0.8: "orange",
                1.0: "red",
            },
        ).add_to(aerial_map)
    folium.LayerControl(collapsed=True).add_to(aerial_map)
    return aerial_map


def build_marker_group(markers, route, pending_marker):
    group = folium.FeatureGroup(name="Custom markers")
    if route:
        folium.PolyLine(
            locations=route["coordinates"],
            color="#d7191c",
            weight=5,
            opacity=0.85,
            tooltip=f"{route['start_title']} to {route['end_title']}",
        ).add_to(group)

    for marker in markers:
        folium.Marker(
            location=[marker["latitude"], marker["longitude"]],
            tooltip=marker["title"],
            popup=folium.Popup(
                safe_popup_html(marker["title"], marker["description"]),
                max_width=350,
            ),
            icon=folium.Icon(
                color=marker.get("color", DEFAULT_MARKER_COLOR),
                icon="info-sign",
            ),
        ).add_to(group)
    if pending_marker:
        folium.Marker(
            location=[pending_marker["latitude"], pending_marker["longitude"]],
            tooltip="New marker location",
            popup="Name this marker in the popup.",
            icon=folium.Icon(color="orange", icon="plus-sign"),
        ).add_to(group)
    return group
