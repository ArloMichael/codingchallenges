import json
import threading
from pathlib import Path

from flask import Flask, render_template
from flask_sock import Sock

from commands import CommandRegistry
from llm import LLMConfig, LLMService
from tooling import ToolRegistry
from tts import load_default_tts, stream_tts_float32_bytes
from weather import WEATHER_TOOL

# This is my custom patched TTS model that runs at 48 kHz
MODEL_PATH = Path("./models/Qwen3-TTS-1.7B-Base-48kHz")

# The voice of Steve Taylor (of Kurzgesagt fame)
REFERENCE_AUDIO = "steve_short.wav"
REFERENCE_TEXT = "Do your past, present and future all exist right now?"

# A decent small LLM (I have tried a good few)
LLM_MODEL_PATH = "mlx-community/Qwen3.5-2B-OptiQ-4bit"
CUSTOM_COMMANDS_PATH = Path("./custom_commands.json")
LOCAL_TIMEZONE = "Australia/Sydney"
SYSTEM_PROMPT = (
    "You are a voice assistant. Answer with no more than one short sentence "
    "and do not use markdown. Use an appropriate available tool whenever the "
    "request requires external information or an action, and never invent tool "
    "results. If required information is missing, ask one short clarifying "
    "question."
)
LLM_MAX_TOKENS = 120

app = Flask(__name__, template_folder="templates")
sock = Sock(app)

generation_lock = threading.Lock()
command_registry = CommandRegistry.from_file(CUSTOM_COMMANDS_PATH)

tts_model, reference_audio = load_default_tts(
    MODEL_PATH,
    REFERENCE_AUDIO,
)
llm = LLMService(
    LLMConfig(
        model_path=LLM_MODEL_PATH,
        system_prompt=SYSTEM_PROMPT,
        timezone=LOCAL_TIMEZONE,
        max_tokens=LLM_MAX_TOKENS,
    ),
    tool_registry=ToolRegistry([WEATHER_TOOL]),
    command_registry=command_registry,
)


@app.route("/")
def index():
    return render_template("index.html")


def normalize_transcript(text):
    return " ".join((text or "").split())


@sock.route("/responses")
def responses_socket(ws):
    # I cannot guarantee perfect context awareness,
    # as the model is non-deterministic in practice,
    # but in my (limited) testing it has proven quite good.
    conversation = llm.create_conversation()
    try:
        while True:
            message = ws.receive()
            if message is None:
                break

            data = json.loads(message or "{}")
            text = normalize_transcript(data.get("text"))
            message_type = data.get("type")

            if not text:
                continue

            if message_type == "interim":
                conversation.preview(text)
                continue

            if message_type == "final":
                response_text = conversation.respond(text)

                if not response_text:
                    continue

                ws.send(json.dumps({"type": "response_text", "text": response_text}))

                with generation_lock:
                    for chunk in stream_tts_float32_bytes(
                        tts_model,
                        reference_audio,
                        text=response_text,
                        ref_text=REFERENCE_TEXT
                    ):
                        ws.send(chunk)

                ws.send(json.dumps({"type": "done"}))

    except Exception as exc:
        try:
            ws.send(json.dumps({"type": "error", "message": str(exc)}))
        except Exception:
            pass
    finally:
        conversation.close()


app.run("0.0.0.0", port=5051, debug=False, threaded=True)
