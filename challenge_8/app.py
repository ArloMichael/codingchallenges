import json
from datetime import date as date_type
from pathlib import Path

import streamlit as st

file_path = Path("db.json")
headings = ["", "Title", "Due Date", "Priority", ""]
column_widths = [0.4, 3, 1.5, 1, 0.35]
priority_colors = {
    "Low": "green",
    "Medium": "orange",
    "High": "red",
}
priority_order = {
    "High": 0,
    "Medium": 1,
    "Low": 2,
    "": 3,
}


def load_rows():
    if not file_path.exists():
        return []
    return json.loads(file_path.read_text(encoding="utf-8"))


def save_rows(rows):
    file_path.write_text(json.dumps(rows, indent=4), encoding="utf-8")


def format_due_date(value):
    due_date = parse_due_date(value)
    if not due_date:
        return ""
    return due_date.strftime("%d/%m/%y")


def parse_due_date(value):
    if isinstance(value, date_type):
        return value
    if not value:
        return None
    return date_type.fromisoformat(value)


def is_overdue(row):
    due_date = parse_due_date(row.get("date"))
    return bool(due_date and due_date < date_type.today())


rows = load_rows()

title_column, sort_column = st.columns([8, 0.6], vertical_alignment="bottom")
title_column.title("Task Manager")
sort_by = "Added Order"
if rows:
    with sort_column:
        with st.popover(":material/filter_list:"):
            sort_by = st.pills(
                "Sort by",
                ["Added Order", "Due Date", "Priority"],
                default="Added Order",
                label_visibility="collapsed",
            )


def sorted_rows(rows, sort_by):
    indexed_rows = list(enumerate(rows))
    if sort_by == "Due Date":
        return sorted(indexed_rows, key=lambda item: item[1].get("date", ""))
    if sort_by == "Priority":
        return sorted(
            indexed_rows,
            key=lambda item: priority_order.get(item[1].get("priority", ""), 3),
        )
    return indexed_rows


def render_task_rows(indexed_rows):
    header = st.columns(column_widths)
    for column, heading in zip(header, headings):
        if heading:
            column.caption(heading)

    for index, row in indexed_rows:
        with st.container():
            columns = st.columns(column_widths, vertical_alignment="center")

            checked = columns[0].checkbox(
                "check",
                value=row.get("check", False),
                key=f"check_{index}",
                label_visibility="collapsed",
            )
            if checked != row.get("check", False):
                rows[index]["check"] = checked
                save_rows(rows)
                st.rerun()

            columns[1].write(row.get("name", ""))
            columns[2].write(format_due_date(row.get("date")))
            priority = row.get("priority", "") or "None"
            columns[3].badge(
                priority,
                color=priority_colors.get(priority, "gray"),
            )

            delete_column, _ = columns[4].columns([1, 1])
            if delete_column.button(
                "",
                key=f"delete_{index}",
                help="Delete task",
                icon=":material/delete:",
                type="tertiary",
            ):
                rows.pop(index)
                save_rows(rows)
                st.rerun()


@st.dialog("Add Task")
def add_row_modal():
    with st.form("add_row", clear_on_submit=True, border=False):
        name = st.text_input("Title")
        date = st.date_input("Date", value=date_type.today())
        priority = st.selectbox(
            "Priority",
            ["Low", "Medium", "High"],
            index=None,
            placeholder="Choose priority",
        )

        if st.form_submit_button("Add Task"):
            if not name or not date:
                st.error("Fill in title and date before adding a row.")
                return

            rows.append(
                {
                    "check": False,
                    "name": name,
                    "date": date.isoformat() if date else None,
                    "priority": priority or "",
                }
            )
            save_rows(rows)
            st.rerun()


if rows:
    ordered_rows = sorted_rows(rows, sort_by)
    done_rows = [item for item in ordered_rows if item[1].get("check", False)]
    open_rows = [item for item in ordered_rows if not item[1].get("check", False)]
    overdue_rows = [item for item in open_rows if is_overdue(item[1])]
    upcoming_rows = [item for item in open_rows if not is_overdue(item[1])]

    if overdue_rows:
        with st.expander("Overdue", expanded=True):
            render_task_rows(overdue_rows)

    if upcoming_rows:
        with st.expander("Upcoming", expanded=True):
            render_task_rows(upcoming_rows)

    if done_rows:
        with st.expander("Done", expanded=False):
            render_task_rows(done_rows)
else:
    st.table({heading: [] for heading in headings})

if st.button("New Task"):
    add_row_modal()
