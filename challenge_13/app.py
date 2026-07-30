import streamlit as st
from streamlit_folium import st_folium

from helpers import (
    DEFAULT_MARKER_COLOR,
    MARKER_COLORS,
    build_aerial_map,
    build_marker_group,
    fetch_osrm_route,
    format_weather,
    load_markers,
    load_weather_for_markers,
    make_marker,
    make_markers_from_csv,
    needs_weather,
    save_markers,
)

st.set_page_config(page_title="Interactive Map", layout="wide")
state = st.session_state
for key, value in {
    "markers": [],
    "pending_marker": None,
    "processed_click": None,
    "markers_loaded": False,
    "route": None,
    "route_error": None,
}.items():
    state.setdefault(key, value)

if not state.markers_loaded:
    state.markers = load_markers()
    state.markers_loaded = True


def clear_route():
    state.route = None
    state.route_error = None


@st.dialog("Add marker")
def render_marker_dialog():
    pending = state.pending_marker
    if pending is None:
        return

    with st.form("new_marker_dialog_form", clear_on_submit=True, border=False):
        title = st.text_input("Title", placeholder="Location name")
        description = st.text_area(
            "Description",
            placeholder="Write some notes here I guess...",
            height=130,
        )
        colors = list(MARKER_COLORS)
        color = st.selectbox(
            "Color",
            colors,
            format_func=lambda value: MARKER_COLORS[value],
            index=colors.index(DEFAULT_MARKER_COLOR),
        )
        save_column, cancel_column = st.columns(2)
        save = save_column.form_submit_button(
            "Save", type="primary", use_container_width=True
        )
        cancel = cancel_column.form_submit_button("Cancel", use_container_width=True)

    if save:
        if not (clean_title := title.strip()):
            st.error("Enter a title.")
        else:
            state.markers.append(
                make_marker(
                    title=clean_title,
                    description=description.strip(),
                    color=color,
                    latitude=pending["latitude"],
                    longitude=pending["longitude"],
                )
            )
            save_markers(state.markers)
            state.pending_marker = None
            st.rerun()
    if cancel:
        state.pending_marker = None
        st.rerun()


st.title("Interactive Map")
st.caption("map huh? *that tracks.*")
show_heatmap = st.toggle("Show marker density", value=False)

map_result = st_folium(
    build_aerial_map(state.markers, show_heatmap=show_heatmap),
    key=f"nsw-aerial-map-heatmap-{show_heatmap}",
    height=720,
    use_container_width=True,
    feature_group_to_add=build_marker_group(
        state.markers, state.route, state.pending_marker
    ),
    returned_objects=["last_clicked"],
)

if clicked := map_result.get("last_clicked") if map_result else None:
    latitude, longitude = float(clicked["lat"]), float(clicked["lng"])
    signature = round(latitude, 7), round(longitude, 7)
    if signature != state.processed_click:
        state.processed_click = signature
        state.pending_marker = {"latitude": latitude, "longitude": longitude}
        st.rerun()

if state.pending_marker is not None:
    render_marker_dialog()

st.subheader("Route")
if len(state.markers) < 2:
    st.caption("You must add at least two markers to calculate a route!")
else:
    markers_by_id = {marker["id"]: marker for marker in state.markers}
    if state.route and not {
        state.route["start_id"],
        state.route["end_id"],
    }.issubset(markers_by_id):
        clear_route()

    marker_ids = list(markers_by_id)
    label = lambda marker_id: markers_by_id[marker_id]["title"]
    start_id = st.selectbox(
        "From", marker_ids, format_func=label, key="route-start-marker"
    )
    end_id = st.selectbox(
        "To",
        [marker_id for marker_id in marker_ids if marker_id != start_id],
        format_func=label,
        key="route-end-marker",
    )
    route_column, clear_column = st.columns(2)
    calculate = route_column.button(
        "Route", type="primary", use_container_width=True
    )
    clear = clear_column.button("Clear", use_container_width=True)

    if calculate:
        try:
            state.route = fetch_osrm_route(
                markers_by_id[start_id], markers_by_id[end_id]
            )
            state.route_error = None
        except RuntimeError as error:
            state.route = None
            state.route_error = str(error)
        st.rerun()
    if clear:
        clear_route()
        st.rerun()
    if state.route:
        distance = state.route["distance_m"] / 1000
        duration = state.route["duration_s"] / 60
        st.success(f"{distance:.2f} km, {duration:.0f} min")
    if state.route_error:
        st.error(state.route_error)


def render_markers(markers):
    widths = [1, 1.5, 1.5, 0.35]
    for column, heading in zip(
        st.columns(widths), ("Title", "Description", "Weather", "")
    ):
        if heading:
            column.caption(heading)

    for marker in markers:
        columns = st.columns(widths, vertical_alignment="center")
        columns[0].write(marker["title"])
        columns[1].write(marker["description"])
        columns[2].write(format_weather(marker))
        delete_column, _ = columns[3].columns([1, 1])
        if delete_column.button(
            "",
            key=f"delete_{marker['id']}",
            help="Delete marker",
            icon=":material/delete:",
            type="tertiary",
        ):
            if state.route and marker["id"] in {
                state.route["start_id"],
                state.route["end_id"],
            }:
                clear_route()
            state.markers = [
                saved for saved in state.markers if saved["id"] != marker["id"]
            ]
            save_markers(state.markers)
            st.rerun()


st.subheader(f"Markers ({len(state.markers)})")
with st.expander("Import markers from CSV"):
    uploaded_csv = st.file_uploader(
        "CSV file", type=["csv"], key="marker-csv-import"
    )
    if uploaded_csv is not None:
        imported, errors = make_markers_from_csv(
            uploaded_csv.getvalue().decode("utf-8-sig")
        )
        if errors:
            st.error("\n".join(errors))
        if imported and st.button(
            f"Import {len(imported)} marker(s)", type="primary"
        ):
            state.markers.extend(imported)
            save_markers(state.markers)
            st.success(f"Imported {len(imported)} marker(s).")
            st.rerun()

if not state.markers:
    st.caption("No saved markers!")
render_markers(state.markers)

if any(needs_weather(marker) for marker in state.markers):
    progress = st.progress(0, text="Loading weather data...")
    load_weather_for_markers(
        state.markers,
        on_progress=lambda done, total: progress.progress(
            done / total if total else 1, text="Loading weather data..."
        ),
    )
    if any(marker.get("weather_error") for marker in state.markers):
        st.warning("Some weather data could not be loaded.")
    progress.empty()
    st.rerun()
