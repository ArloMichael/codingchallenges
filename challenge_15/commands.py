import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


COMMAND_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]{0,63}$")
TRAILING_PUNCTUATION = " \t\r\n.!?"


class CommandConfigError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CustomCommand:
    name: str
    phrases: tuple
    response: str

    def __post_init__(self):
        name = self.name.strip()
        response = self.response.strip()
        phrases = tuple(phrase.strip() for phrase in self.phrases)

        if not COMMAND_NAME_PATTERN.fullmatch(name):
            raise CommandConfigError(f"Invalid command name: {self.name!r}")
        if not phrases or any(not phrase for phrase in phrases):
            raise CommandConfigError(
                f"Command {name!r} requires at least one non-empty phrase."
            )
        if not response:
            raise CommandConfigError(
                f"Command {name!r} requires a non-empty response."
            )

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "phrases", phrases)
        object.__setattr__(self, "response", response)


class CommandRegistry:
    def __init__(self, commands=()):
        self._commands = {}
        self._phrases = {}

        for command in commands:
            self.register(command)

    def register(self, command):
        if not isinstance(command, CustomCommand):
            raise TypeError("Only CustomCommand instances can be registered.")
        if command.name in self._commands:
            raise CommandConfigError(
                f"Command {command.name!r} is already registered."
            )

        normalized_phrases = []
        for phrase in command.phrases:
            normalized = normalize_command_text(phrase)
            if normalized in self._phrases or normalized in normalized_phrases:
                raise CommandConfigError(
                    f"Command phrase {phrase!r} is already registered."
                )
            normalized_phrases.append(normalized)

        self._commands[command.name] = command
        for phrase in normalized_phrases:
            self._phrases[phrase] = command

        return command

    @classmethod
    def from_file(cls, path):
        config_path = Path(path)

        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except OSError as error:
            raise CommandConfigError(
                f"Could not read command config {config_path}: {error}"
            ) from error
        except json.JSONDecodeError as error:
            raise CommandConfigError(
                f"Invalid JSON in command config {config_path}: {error}"
            ) from error

        commands = _parse_commands(data)
        return cls(commands)

    @property
    def names(self):
        return tuple(self._commands)

    def find(self, text):
        return self._phrases.get(normalize_command_text(text))

    def response_for(self, text):
        command = self.find(text)
        return command.response if command is not None else None


def normalize_command_text(text):
    if not isinstance(text, str):
        return ""

    normalized = unicodedata.normalize("NFKC", text)
    normalized = " ".join(normalized.split())
    return normalized.rstrip(TRAILING_PUNCTUATION).casefold()


def _parse_commands(data):
    if not isinstance(data, dict):
        raise CommandConfigError("Command config must be a JSON object.")

    entries = data.get("commands")
    if not isinstance(entries, list):
        raise CommandConfigError("Command config requires a commands array.")

    commands = []
    allowed_fields = {"name", "phrases", "response"}

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise CommandConfigError(
                f"Command at index {index} must be a JSON object."
            )

        unknown_fields = set(entry) - allowed_fields
        if unknown_fields:
            fields = ", ".join(sorted(unknown_fields))
            raise CommandConfigError(
                f"Command at index {index} has unknown fields: {fields}."
            )

        name = entry.get("name")
        phrases = entry.get("phrases")
        response = entry.get("response")
        if not isinstance(name, str):
            raise CommandConfigError(
                f"Command at index {index} requires a string name."
            )
        if not isinstance(phrases, list) or not all(
            isinstance(phrase, str) for phrase in phrases
        ):
            raise CommandConfigError(
                f"Command {name!r} requires an array of string phrases."
            )
        if not isinstance(response, str):
            raise CommandConfigError(
                f"Command {name!r} requires a string response."
            )

        commands.append(
            CustomCommand(
                name=name,
                phrases=tuple(phrases),
                response=response,
            )
        )

    return commands
