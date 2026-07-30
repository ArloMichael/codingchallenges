import json
import questionary
from pathlib import Path
from decimal import Decimal
from datetime import datetime
import matplotlib.pyplot as plt

path = "db.json"
init = {
    "expenses": [],
    "income": [],
}

try:
    with open(path, "r") as file:
        content = json.load(file)

except FileNotFoundError:
    option = questionary.select(
        "The database file does not exist.",
        choices=[
            "Create one",
            "Pick a file",
            "Exit",
        ],
        erase_when_done=True,
    ).ask()

    match option:
        case "Create one":
            with open(path, "w") as file:
                json.dump(init, file, indent=4)

            content = init

        case "Pick a file":
            path = questionary.path(
                "What is the filepath?",
                validate=lambda x: (x != "" and Path(x).exists()),
            ).ask()

            path = Path(path).expanduser()
            
            with open(path, "r") as file:
                content = json.load(file)

        case "Exit" | None:
            raise SystemExit

def is_valid_amount(x):
    try:
        return False if Decimal(x) == 0 else True
    except Exception as e:
        return False
    
def is_valid_date(date_string):
    try:
        datetime.strptime(date_string, "%d/%m/%y")
        return True
    except ValueError:
        return False
    
def is_valid_month(date_string):
    try:
        datetime.strptime(date_string, "%m/%y")
        return True
    except ValueError:
        return False

def add_income():
    income_amount = Decimal(questionary.text(
        "Amount ($)",
        erase_when_done=True,
        validate=is_valid_amount
    ).ask())

    income_date = questionary.text(
        "Date",
        instruction="DD/MM/YY",
        validate=is_valid_date,
        erase_when_done=True,
    ).ask()

    content["income"].append({"date": datetime.strptime(income_date, "%d/%m/%y").isoformat(), "amount": str(income_amount)})

    with open(path, "w") as file:
        json.dump(content, file, indent=4)

def add_expense():
    expense_type = questionary.select(
        "Expense Type",
        choices=[
            "Food",
            "Rent",
            "Transport",
            "Entertainment",
            "Utilities",
            "Other",
            "Back",
        ],
        erase_when_done=True,
    ).ask()

    if expense_type in ("Back", None):
        return
    
    expense_date = questionary.text(
        "Date",
        instruction="DD/MM/YY",
        validate=is_valid_date,
        erase_when_done=True,
    ).ask()
    
    expense_amount = Decimal(questionary.text(
        "Amount ($)",
        erase_when_done=True,
        validate=is_valid_amount
    ).ask())

    content["expenses"].append({"date": datetime.strptime(expense_date, "%d/%m/%y").isoformat(), "type": expense_type, "amount": str(expense_amount)})

    with open(path, "w") as file:
        json.dump(content, file, indent=4)

def view_balance():
    print(f"Current balance: \033[3m${sum([Decimal(x["amount"]) for x in list(content["income"])]) - sum([Decimal(x["amount"]) for x in list(content["expenses"])]):,.2f}\033[0m", end="", flush=True)
    questionary.press_any_key_to_continue(
        message="\nPress any key to return...",
        erase_when_done=True,
    ).ask()

def view_summary():
    summary = {
        "Food": Decimal(0),
        "Rent": Decimal(0),
        "Transport": Decimal(0),
        "Entertainment": Decimal(0),
        "Utilities": Decimal(0),
        "Other": Decimal(0),
    }

    for cost in content["expenses"]:
        summary[cost["type"]] += Decimal(cost["amount"])

    print(" | ".join([f"{category[0]}: \033[3m${category[1]}\033[0m" for category in zip(summary.keys(), summary.values())]), end="", flush=True)
    questionary.press_any_key_to_continue(
        message="\nPress any key to return...",
        erase_when_done=True,
    ).ask()

def view_graph():
    summary = {
        "Food": 0,
        "Rent": 0,
        "Transport": 0,
        "Entertainment": 0,
        "Utilities": 0,
        "Other": 0,
    }

    for cost in content["expenses"]:
        summary[cost["type"]] += float(cost["amount"])

    x = list(summary.keys())
    y = list(summary.values())

    plt.pie(y, labels = x)
    plt.title("Lifetime expendature per category")
    plt.show()

def view_month():
    check_date = questionary.text(
        "Date",
        instruction="MM/YY",
        validate=is_valid_month,
        erase_when_done=True,
    ).ask()

    summary = {
        "Food": Decimal(0),
        "Rent": Decimal(0),
        "Transport": Decimal(0),
        "Entertainment": Decimal(0),
        "Utilities": Decimal(0),
        "Other": Decimal(0),
    }

    for cost in content["expenses"]:
        cost_date = datetime.fromisoformat(cost["date"])
        selected_date = datetime.strptime(check_date, "%m/%y")

        if (cost_date.year == selected_date.year) and (cost_date.month == selected_date.month):
            summary[cost["type"]] += Decimal(cost["amount"])

    print(" | ".join([f"{category[0]}: \033[3m${category[1]}\033[0m" for category in zip(summary.keys(), summary.values())]), end="", flush=True)
    questionary.press_any_key_to_continue(
        message="\nPress any key to return...",
        erase_when_done=True,
    ).ask()

def main():
    while True:
        choice = questionary.select(
            "Expense Tracker",
            choices=[
                "Add income",
                "Add an expense",
                "View balance",
                "View monthly expendature",
                "View lifetime expendature (graph)",
                "View lifetime expendature (categorised)",
                "Exit",
            ],
            erase_when_done=True,
        ).ask()

        match choice:
            case "Add income":
                add_income()

            case "Add an expense":
                add_expense()

            case "View balance":
                view_balance()

            case "View monthly expendature":
                view_month()

            case "View lifetime expendature (graph)":
                view_graph()

            case "View lifetime expendature (categorised)":
                view_summary()

            case "Exit" | None:
                break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass