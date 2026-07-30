import json
import questionary
from pathlib import Path

text = (
    "You awake in a locked room. Inside is a desk, bookshelf, and safe. Escape..."
)

DEFAULT_SOLVED = {
    "riddle": False,
    "lock": False,
    "cipher": False,
}
DEFAULT_TURNS_LEFT = 6
ENDINGS = {
    "escaped": "The iron key turns in the door. You step into the hallway and escape.",
    "trapped": "Out of turns. The room locks forever...",
    "secret_room": "The brass token opens a hidden panel behind the safe. You unlock the secret room.",
}
ITEMS = {
    "desk_note": {
        "name": "Desk note",
        "use": "The note reads: It repeats what it hears.",
    },
    "brass_token": {
        "name": "Brass token",
        "use": "You turn the brass token over. Its edge is stamped with a tiny safe symbol.",
    },
    "glass_lens": {
        "name": "Glass lens",
        "use": "Through the glass lens, shifted letters look one step clearer.",
    },
    "iron_key": {
        "name": "Iron key",
        "use": "The iron key is heavy enough to turn the room's final lock.",
    },
}
PUZZLE_REWARDS = {
    "riddle": "brass_token",
    "lock": "glass_lens",
    "cipher": "iron_key",
}


def response(message):
    print(f"\r{message}", end="", flush=True)


def new_state():
    return {
        "solved": DEFAULT_SOLVED.copy(),
        "turns_left": DEFAULT_TURNS_LEFT,
        "inventory": [],
        "ending": None,
    }


def load_game(path):
    with open(path, "r") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Save file must contain a JSON object.")

    solved = data.get("solved")
    turns_left = data.get("turns_left")
    inventory = data.get("inventory")
    ending = data.get("ending")

    if not isinstance(solved, dict):
        raise ValueError("Save file is missing solved puzzle state.")

    if not isinstance(turns_left, int):
        raise ValueError("Save file is missing turns_left.")

    if not isinstance(inventory, list):
        raise ValueError("Save file inventory must be a list.")

    if "ending" not in data:
        raise ValueError("Save file is missing ending state.")

    if ending is not None and ending not in ENDINGS:
        raise ValueError("Save file has an unknown ending.")

    solved_state = {
        puzzle: bool(solved.get(puzzle, False))
        for puzzle in DEFAULT_SOLVED
    }
    inventory_state = [
        item
        for item in inventory
        if isinstance(item, str) and item in ITEMS
    ]

    return {
        "solved": solved_state,
        "turns_left": max(0, turns_left),
        "inventory": inventory_state,
        "ending": ending,
    }


def save_game(path, state):
    with open(path, "w") as file:
        json.dump(
            state,
            file,
            indent=2,
        )
        file.write("\n")


def is_new_json_path(path):
    path = Path(path).expanduser()
    return (
        path.name != ""
        and path.parent.exists()
        and not path.exists()
        and path.suffix.lower() == ".json"
    )


def is_existing_json_path(path):
    path = Path(path).expanduser()
    return path.is_file() and path.suffix.lower() == ".json"


def add_item(inventory, item):
    if item not in inventory:
        inventory.append(item)
        response(f"Added to inventory: {ITEMS[item]['name']}.")
        return True

    response(f"You already have the {ITEMS[item]['name']}.")
    return False


def item_name(item):
    return ITEMS[item]["name"]


def show_inventory(inventory):
    if not inventory:
        response("Inventory is empty.")
        return

    response("Inventory: " + ", ".join(item_name(item) for item in inventory))


def use_inventory_item(inventory, solved):
    if not inventory:
        response("Inventory is empty.")
        return None

    choices = [item_name(item) for item in inventory] + ["Back"]
    choice = questionary.select("Use item", choices=choices, erase_when_done=True).ask()

    if choice in (None, "Back"):
        return None

    item = next(item for item in inventory if item_name(item) == choice)
    response(ITEMS[item]["use"])

    if item == "brass_token" and all(solved.values()):
        if "glass_lens" in inventory:
            response(ENDINGS["secret_room"])
            print()
            return "secret_room"

        response("The token is warm, but you cannot see where it fits.")

    if item == "iron_key":
        if all(solved.values()):
            response(ENDINGS["escaped"])
            print()
            return "escaped"

        response("The iron key does not fit anything useful yet.")

    return None


def riddle():
    answer = questionary.text(
        'You notice a note on the desk. You read, "reverb"',
        erase_when_done=True,
    ).ask()

    if answer and answer.strip().lower() == "echo":
        response("Desk solved: you found a brass token.")
        return True

    response("Wrong. Hint: it repeats what it hears.")
    return False

def lock():
    answer = questionary.text(
        "Safe clue: double 21, then add 3.",
        erase_when_done=True,
    ).ask()

    if answer and answer.strip() == "45":
        response("Safe solved: you found a glass lens.")
        return True

    response("Wrong. Hint: (21 * 2) + 3.")
    return False

def cipher():
    answer = questionary.text(
        "Bookshelf cipher: Uif qbttxpse jt GSFFEPN",
        erase_when_done=True,
    ).ask()

    if answer and answer.strip().lower() == "freedom":
        response("Cipher solved: the door latch appears.")
        return True

    response("Wrong. Hint: shift each letter back by 1.")
    return False

def status(solved, turns_left, inventory):
    return (
        f"Progress: {sum(solved.values())}/3 solved | "
        f"Turns {turns_left} | "
        f"Items {len(inventory)} | "
        f"Desk {'done' if solved['riddle'] else 'locked'} | "
        f"Safe {'done' if solved['lock'] else 'locked'} | "
        f"Cipher {'done' if solved['cipher'] else 'locked'}"
    )

def main():
    type_game = questionary.select("Start Game", choices=["From File", "New"]).ask()

    match type_game:

        case "From File":
            path = questionary.path("Load file", validate=is_existing_json_path).ask()

            if not path:
                exit()

            path = Path(path).expanduser()
            try:
                state = load_game(path)
            except (json.JSONDecodeError, OSError, ValueError) as error:
                response(f"Could not load save file: {error}")
                print()
                exit()

        case "New":
            path = questionary.path("New file", validate=is_new_json_path).ask()

            if not path:
                exit()

            path = Path(path).expanduser()
            state = new_state()
            save_game(path, state)

        case None:
            exit()

    solved = state["solved"]
    turns_left = state["turns_left"]
    inventory = state["inventory"]
    response(text)

    while state["ending"] is None and turns_left > 0:
        choice = questionary.select(
            status(solved, turns_left, inventory),
            choices=[
                "Search room",
                "Riddle",
                "Lock puzzle",
                "Cipher challenge",
                "Inventory",
                "Exit",
            ],
            erase_when_done=True,
            instruction=text
        ).ask()

        match choice:
            case "Search room":
                add_item(inventory, "desk_note")
                save_game(path, state)

            case "Riddle":
                if solved["riddle"]:
                    response("Desk already solved.")
                else:
                    turns_left -= 1
                    solved["riddle"] = riddle()
                    if solved["riddle"]:
                        add_item(inventory, PUZZLE_REWARDS["riddle"])
                    state["turns_left"] = turns_left
                    save_game(path, state)

            case "Lock puzzle":
                if solved["lock"]:
                    response("Safe already solved.")
                else:
                    turns_left -= 1
                    solved["lock"] = lock()
                    if solved["lock"]:
                        add_item(inventory, PUZZLE_REWARDS["lock"])
                    state["turns_left"] = turns_left
                    save_game(path, state)

            case "Cipher challenge":
                if solved["cipher"]:
                    response("Cipher already solved.")
                else:
                    turns_left -= 1
                    solved["cipher"] = cipher()
                    if solved["cipher"]:
                        add_item(inventory, PUZZLE_REWARDS["cipher"])
                    state["turns_left"] = turns_left
                    save_game(path, state)

            case "Inventory":
                show_inventory(inventory)
                ending = use_inventory_item(inventory, solved)
                if ending is not None:
                    state["ending"] = ending
                    save_game(path, state)

            case "Exit" | None:
                confirm = questionary.confirm("Are you sure you want to exit?", auto_enter=False).ask()
                if confirm:
                    break

    if state["ending"] is not None:
        return
    elif all(solved.values()):
        state["ending"] = "escaped"
        save_game(path, state)
        response(ENDINGS["escaped"])
        print()
    elif turns_left == 0:
        state["ending"] = "trapped"
        save_game(path, state)
        response(ENDINGS["trapped"])
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
