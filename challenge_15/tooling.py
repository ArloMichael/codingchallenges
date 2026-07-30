import json
import re
from copy import deepcopy
from dataclasses import dataclass
from inspect import Parameter, signature
from typing import Callable


TOOL_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]{0,63}$")


class ToolError(Exception):
    """An expected error that is safe to return to the model."""


@dataclass(frozen=True, slots=True)
class Tool:
    name: str
    description: str
    parameters: dict
    handler: Callable

    def __post_init__(self):
        if not TOOL_NAME_PATTERN.fullmatch(self.name):
            raise ValueError(f"Invalid tool name: {self.name!r}")
        if not self.description.strip():
            raise ValueError(f"Tool {self.name!r} requires a description.")
        if self.parameters.get("type") != "object":
            raise ValueError(
                f"Tool {self.name!r} parameters must be a JSON object schema."
            )
        if not callable(self.handler):
            raise TypeError(f"Tool {self.name!r} handler must be callable.")

    def schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": deepcopy(self.parameters),
            },
        }


class ToolRegistry:
    def __init__(self, tools=()):
        self._tools = {}
        for tool in tools:
            self.register(tool)

    def register(self, tool):
        if not isinstance(tool, Tool):
            raise TypeError("Only Tool instances can be registered.")
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name!r} is already registered.")

        self._tools[tool.name] = tool
        return tool

    @property
    def schemas(self):
        return [tool.schema() for tool in self._tools.values()]

    @property
    def names(self):
        return tuple(self._tools)

    def execute(self, name, arguments):
        tool = self._tools.get(name)
        if tool is None:
            return _tool_error("unknown_tool", f"Unknown tool: {name}")
        if not isinstance(arguments, dict):
            return _tool_error(
                "invalid_arguments",
                "Tool arguments must be an object.",
            )

        binding_error = _validate_handler_arguments(tool, arguments)
        if binding_error is not None:
            return _tool_error("invalid_arguments", binding_error)

        try:
            result = tool.handler(**arguments)
        except ToolError as error:
            return _tool_error("tool_error", str(error))
        except Exception:
            return _tool_error(
                "execution_failed",
                f"The {name} tool failed unexpectedly.",
            )

        try:
            json.dumps(result)
        except (TypeError, ValueError):
            return _tool_error(
                "invalid_result",
                f"The {name} tool returned an invalid result.",
            )

        return result


def _validate_handler_arguments(tool, arguments):
    try:
        handler_signature = signature(tool.handler)
    except (TypeError, ValueError):
        return None

    if any(
        parameter.kind == Parameter.POSITIONAL_ONLY
        for parameter in handler_signature.parameters.values()
    ):
        return f"The {tool.name} tool cannot accept named arguments."

    try:
        handler_signature.bind(**arguments)
    except TypeError as error:
        return str(error)

    return None


def _tool_error(code, message):
    return {
        "error": {
            "code": code,
            "message": message,
        }
    }
