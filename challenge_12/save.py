import json
from pathlib import Path

from pet import Pet


SAVE_VERSION = 1


def save_exists(path):
    return Path(path).is_file()


def save_pet(path, pet):
    path = Path(path)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    payload = {
        "version": SAVE_VERSION,
        "pet": pet.to_dict(),
    }

    temporary_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    temporary_path.replace(path)


def load_pet(path):
    path = Path(path)

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Could not read the save file") from error

    if not isinstance(payload, dict) or payload.get("version") != SAVE_VERSION:
        raise ValueError("Unsupported save-file version")

    return Pet.from_dict(payload.get("pet"))
