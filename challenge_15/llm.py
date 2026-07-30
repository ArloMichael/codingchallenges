import json
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from mlx_lm import load

from agent import generate
from commands import CommandRegistry
from tooling import ToolRegistry


MAX_TOOL_ROUNDS = 2
TOOL_FAILURE_RESPONSE = "I couldn't complete that request."


@dataclass(frozen=True)
class LLMConfig:
    model_path: str
    system_prompt: str
    timezone: str = "Australia/Sydney"
    max_tokens: int = 120


class LLMService:
    def __init__(
        self,
        config,
        tool_registry=None,
        command_registry=None,
    ):
        self.config = config
        self.timezone = ZoneInfo(config.timezone)
        self.model, self.tokenizer = load(config.model_path)
        self.tool_registry = (
            tool_registry if tool_registry is not None else ToolRegistry()
        )
        self.command_registry = (
            command_registry if command_registry is not None else CommandRegistry()
        )

    def create_conversation(self):
        return Conversation(self)

    def build_system_prompt(self):
        now = datetime.now(self.timezone)
        return (
            f"{self.config.system_prompt}\n"
            f"Current local date and time: {now.isoformat(timespec='seconds')} "
            f"({self.config.timezone})."
        )

    @property
    def tool_schemas(self):
        return self.tool_registry.schemas

    def execute_tool(self, name, arguments):
        return self.tool_registry.execute(name, arguments)

    def command_response(self, text):
        return self.command_registry.response_for(text)


class Conversation:
    def __init__(self, service):
        self.service = service
        self.history = []
        self.current_prompt = ""
        self.current_generation = None

    def _messages(self, text):
        return [
            {
                "role": "system",
                "content": self.service.build_system_prompt(),
            },
            *self.history,
            {"role": "user", "content": text},
        ]

    def _start(self, text):
        self.cancel()
        self.current_prompt = text
        self.current_generation = generate(
            self.service.model,
            self.service.tokenizer,
            self._messages(text),
            max_tokens=self.service.config.max_tokens,
            tools=self.service.tool_schemas,
        )

    def preview(self, text):
        """Speculatively generate a response for an interim transcript."""
        if text != self.current_prompt:
            self._start(text)

    def respond(self, text):
        """Return a response and commit the final exchange to the history."""
        command_response = self.service.command_response(text)
        if command_response is not None:
            self.cancel()
            self.history.extend(
                [
                    {"role": "user", "content": text},
                    {"role": "assistant", "content": command_response},
                ]
            )
            return command_response

        if text != self.current_prompt or self.current_generation is None:
            self._start(text)

        generation = self.current_generation

        try:
            response = generation.wait().strip()
        finally:
            self.current_generation = None
            self.current_prompt = ""

        turn_messages = [{"role": "user", "content": text}]
        generation_messages = self._messages(text)

        for _ in range(MAX_TOOL_ROUNDS):
            parsed = self._parse_tool_call(response)
            if parsed is None:
                if self._contains_tool_call(response):
                    response = TOOL_FAILURE_RESPONSE
                break

            call, preamble = parsed
            assistant_message = {
                "role": "assistant",
                "content": preamble,
                "tool_calls": [
                    {
                        "type": "function",
                        "function": call,
                    }
                ],
            }
            result = self.service.execute_tool(
                call["name"],
                call["arguments"],
            )
            tool_message = {
                "role": "tool",
                "content": json.dumps(result, ensure_ascii=False),
            }

            turn_messages.extend([assistant_message, tool_message])
            generation_messages.extend([assistant_message, tool_message])
            response = generate(
                self.service.model,
                self.service.tokenizer,
                generation_messages,
                max_tokens=self.service.config.max_tokens,
                tools=self.service.tool_schemas,
            ).wait().strip()
        else:
            if self._contains_tool_call(response):
                response = TOOL_FAILURE_RESPONSE

        if response:
            turn_messages.append({"role": "assistant", "content": response})
            self.history.extend(turn_messages)

        return response

    def _contains_tool_call(self, text):
        start_marker = self.service.tokenizer.tool_call_start
        return bool(start_marker and start_marker in text)

    def _parse_tool_call(self, text):
        tokenizer = self.service.tokenizer
        start_marker = tokenizer.tool_call_start
        end_marker = tokenizer.tool_call_end

        if not start_marker or not end_marker:
            return None

        start = text.find(start_marker)
        if start == -1:
            return None

        end = text.find(end_marker, start + len(start_marker))
        if end == -1:
            return None

        tool_text = text[start + len(start_marker) : end].strip()

        try:
            call = tokenizer.tool_parser(tool_text, self.service.tool_schemas)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

        if isinstance(call, list):
            if len(call) != 1:
                return None
            call = call[0]

        if not isinstance(call, dict):
            return None

        name = call.get("name")
        arguments = call.get("arguments")
        if not isinstance(name, str) or not isinstance(arguments, dict):
            return None

        return {"name": name, "arguments": arguments}, text[:start].strip()

    def cancel(self):
        generation = self.current_generation
        self.current_generation = None
        self.current_prompt = ""

        if generation is not None and not generation.done.is_set():
            generation.cancel()
            generation.done.wait()

    def close(self):
        self.cancel()
