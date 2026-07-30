from datetime import time
import argparse
from rich.console import Console
from rich.layout import Layout
from rich.table import Table

period_times = [
    {"start": time(8, 30), "end": time(8, 47)},
    {"start": time(8, 48), "end": time(9, 50)},
    {"start": time(9, 51), "end": time(10, 53)},
    {"start": time(11, 13), "end": time(12, 15)},
    {"start": time(12, 16), "end": time(13, 18)},
    {"start": time(13, 58), "end": time(14, 59)},
]

timetable = {
    1: [
        {"id": 0, "name": "Roll Call", "room": "E2"},
        {"id": 1, "name": "Computing Technology", "room": "C2"}, 
        {"id": 2, "name": "English", "room": "B11"},
        {"id": 3, "name": "Health", "room": "E2"},
        {"id": 4, "name": "Maths", "room": "E4"},
        {"id": 5, "name": "Geography", "room": "B7"},
    ],
    2: [
        {"id": 0, "name": "Roll Call", "room": "E2"},
        {"id": 1, "name": "Geography", "room": "B7"}, 
        {"id": 2, "name": "Science", "room": "L3"},
        {"id": 3, "name": "Music", "room": "P2"},
        {"id": 4, "name": "History", "room": "H2"},
        {"id": 5, "name": "English", "room": "B11"},
    ],
    3: [
        {"id": 0, "name": "Roll Call", "room": "E2"},
        {"id": 1, "name": "Sport", "room": "RLC2"}, 
        {"id": 2, "name": "Music", "room": "P2"},
        {"id": 3, "name": "Maths", "room": "E4"},
        {"id": 4, "name": "History", "room": "H2"},
        {"id": 5, "name": "English", "room": "B11"},
    ],
    4: [
        {"id": 0, "name": "Roll Call", "room": "E2"},
        {"id": 1, "name": "Religion", "room": "I6"}, 
        {"id": 2, "name": "Science", "room": "L2"},
        {"id": 3, "name": "English", "room": "B11"},
        {"id": 4, "name": "HF/Service", "room": "A3"},
        {"id": 5, "name": "Maths", "room": "E4"},
    ],
    5: [
        {"id": 0, "name": "", "room": ""},
        {"id": 1, "name": "Maths", "room": "E4"}, 
        {"id": 2, "name": "Science", "room": "L7"},
        {"id": 3, "name": "Geography", "room": "B7"},
        {"id": 4, "name": "Computing Technology", "room": "C2"},
        {"id": 5, "name": "Music", "room": "P3"},
    ],
    6: [
        {"id": 0, "name": "Roll Call", "room": "E2"},
        {"id": 1, "name": "Maths", "room": "E4"}, 
        {"id": 2, "name": "Computing Technology", "room": "C2"},
        {"id": 3, "name": "Religion", "room": "H3"},
        {"id": 4, "name": "English", "room": "B11"},
        {"id": 5, "name": "Sport", "room": "MSF"},
    ],
    7: [
        {"id": 0, "name": "Roll Call", "room": "E2"},
        {"id": 1, "name": "Maths", "room": "E4"}, 
        {"id": 2, "name": "Science", "room": "L2"},
        {"id": 3, "name": "Health", "room": "F1"},
        {"id": 4, "name": "Geography", "room": "B8"},
        {"id": 5, "name": "Computing Technology", "room": "C2"},
    ],
    8: [
        {"id": 0, "name": "Roll Call", "room": "E2"},
        {"id": 1, "name": "SSA", "room": "NOR"}, 
        {"id": 2, "name": "Science", "room": "L2"},
        {"id": 3, "name": "Leadership", "room": "A3"},
        {"id": 4, "name": "Maths", "room": "E4"},
        {"id": 5, "name": "History", "room": "B1"},
    ],
    9: [
        {"id": 0, "name": "Roll Call", "room": "E2"},
        {"id": 1, "name": "English", "room": "B11"}, 
        {"id": 2, "name": "Science", "room": "L3"},
        {"id": 3, "name": "Music", "room": "E2"},
        {"id": 4, "name": "HF/Service", "room": "A3"},
        {"id": 5, "name": "Religion", "room": "H4"},
    ],
    10: [
        {"id": 0, "name": "", "room": ""},
        {"id": 1, "name": "Music", "room": "P2"}, 
        {"id": 2, "name": "Science", "room": "L3"},
        {"id": 3, "name": "Computing Technology", "room": "C2"},
        {"id": 4, "name": "English", "room": "B11"},
        {"id": 5, "name": "History", "room": "B5"},
    ],
}

def num_to_day(n):
    return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"][(n - 1) % 5]

def week_name(day):
    return "Week A" if day <= 5 else "Week B"

def add_class(day, period, name, room=""):
    timetable[day][period] = {"id": period, "name": name, "room": room}

def remove_class(day, period):
    timetable[day][period] = {"id": period, "name": "", "room": ""}

def modify_class(day, period, name=None, room=None):
    if name is not None:
        timetable[day][period]["name"] = name
    if room is not None:
        timetable[day][period]["room"] = room

def print_subject_matches(text):
    found = False
    for day, classes in timetable.items():
        for lesson in classes:
            if lesson["name"].lower() == text.lower():
                print(
                    f"{text}: {week_name(day)} {num_to_day(day)}, "
                    f"Period {lesson['id']} ({lesson['room']})"
                )
                found = True

    if not found:
        print(f"Subject '{text}' not found.")
        exit()

def print_free_periods():
    found = False
    for day, classes in timetable.items():
        for lesson in classes:
            if lesson["name"] == "":
                print(f"Free: {week_name(day)} {num_to_day(day)}, Period {lesson['id']}")
                found = True

    if not found:
        print("No free periods found.")

def get_table_for_days(a, b, timetable, highlight="", title="Unnamed"):
    table = Table(title=title, width=120)

    table.add_column("", justify="right", no_wrap=True)
    table.add_column("Monday", style="red")
    table.add_column("Tuesday", style="blue")
    table.add_column("Wednesday", style="purple")
    table.add_column("Thursday", style="yellow")
    table.add_column("Friday", style="green")

    for period in range(0,6):
        start = period_times[period]["start"].strftime("%H:%M")
        end = period_times[period]["end"].strftime("%H:%M")
        row = [f"{start} - {end}"]
        for x in list(timetable.values())[a:b]:
            if highlight == x[period]["name"].lower():
                row.append(f"[bold]{x[period]["name"]}[/bold]")
            else:
                row.append(x[period]["name"])

        table.add_row(*row)

    return table

highlight = ""

parser = argparse.ArgumentParser(description="Timetable")
subparsers = parser.add_subparsers(dest="mode", help="Select the mode")

add_parser = subparsers.add_parser("add", help="Add a class to the timetable in memory")
add_parser.add_argument("--day", type=int, choices=range(1, 11), required=True, help="Day number from 1 to 10")
add_parser.add_argument("--period", type=int, choices=range(0, 6), required=True, help="Period number from 0 to 5")
add_parser.add_argument("--name", required=True, help="Class name")
add_parser.add_argument("--room", help="Class room")

remove_parser = subparsers.add_parser("remove", help="Remove a class from the timetable in memory")
remove_parser.add_argument("--day", type=int, choices=range(1, 11), required=True, help="Day number from 1 to 10")
remove_parser.add_argument("--period", type=int, choices=range(0, 6), required=True, help="Period number from 0 to 5")

modify_parser = subparsers.add_parser("modify", help="Modify the timetable in memory (change the name of a subject)")
modify_parser.add_argument("--day", type=int, choices=range(1, 11), required=True, help="Day number from 1 to 10")
modify_parser.add_argument("--period", type=int, choices=range(0, 6), required=True, help="Period number from 0 to 5")
modify_parser.add_argument("--name", help="Class name")
modify_parser.add_argument("--room", help="Class room")

search_parser = subparsers.add_parser("search", help="Search for a subject")
search_parser.add_argument("text", help="Subject to search for")

subparsers.add_parser("free", help="Find free periods")

args = parser.parse_args()

match args.mode:
    case "add":
        add_class(args.day, args.period, args.name, args.room or "")
    case "remove":
        remove_class(args.day, args.period)
    case "modify":
        modify_class(args.day, args.period, args.name, args.room)
    case "search":
        print_subject_matches(args.text)
        highlight = args.text.lower()
    case "free":
        print_free_periods()
    case None:
        pass


layout = Layout()
layout.split_column(
    Layout(get_table_for_days(0, 5, timetable, title="Week A", highlight=highlight)),
    Layout(get_table_for_days(5, 10, timetable, title="Week B", highlight=highlight))
)

console = Console()
console.print(layout)
