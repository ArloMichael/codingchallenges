from threading import Event, Thread
from mlx_lm import stream_generate


class Generation:
    def __init__(self, model, tokenizer, prompt, max_tokens=4096, stop=None):
        self.model = model
        self.tokenizer = tokenizer
        self.prompt = prompt
        self.max_tokens = max_tokens
        self.stop = stop

        self.cancelled = Event()
        self.done = Event()
        self.text = ""
        self.error = None
        self.thread = Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()
        return self

    def cancel(self):
        self.cancelled.set()

    def wait(self):
        self.done.wait()
        if self.error is not None:
            raise self.error
        return self.text

    def _run(self):
        try:
            for chunk in stream_generate(
                self.model,
                self.tokenizer,
                self.prompt,
                max_tokens=self.max_tokens,
            ):
                if self.cancelled.is_set() or (self.stop and self.stop(chunk.text)):
                    break

                self.text += chunk.text
        except Exception as error:
            self.error = error
        finally:
            self.done.set()


def generate(model, tokenizer, messages, max_tokens=4096, tools=None):
    template_options = {
        "tokenize": False,
        "add_generation_prompt": True,
        "enable_thinking": False,
    }
    if tools:
        template_options["tools"] = tools

    prompt = tokenizer.apply_chat_template(messages, **template_options)

    return Generation(model, tokenizer, prompt, max_tokens).start()
