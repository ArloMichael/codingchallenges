import json
import shutil
from pathlib import Path

from huggingface_hub import snapshot_download


TTS_REPO = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-4bit"

TOKENIZER_48K_REPO = "takuma104/Qwen3-TTS-Tokenizer-12Hz-48kHz"

OUTPUT_DIR = Path("./Qwen3-TTS-1.7B-Base-48kHz")


def main():
    snapshot_download(
        repo_id=TTS_REPO,
        local_dir=OUTPUT_DIR,
    )

    tokenizer_source = Path(
        snapshot_download(
            repo_id=TOKENIZER_48K_REPO,
            allow_patterns=[
                "config.json",
                "model.safetensors",
                "preprocessor_config.json",
            ],
        )
    )

    tokenizer_destination = OUTPUT_DIR / "speech_tokenizer"
    shutil.rmtree(tokenizer_destination, ignore_errors=True)
    tokenizer_destination.mkdir(parents=True)

    for filename in [
        "config.json",
        "model.safetensors",
        "preprocessor_config.json",
    ]:
        source_file = tokenizer_source / filename
        if source_file.exists():
            shutil.copy2(source_file, tokenizer_destination / filename)

    root_config_path = OUTPUT_DIR / "config.json"

    with root_config_path.open("r", encoding="utf-8") as file:
        root_config = json.load(file)

    root_config["sample_rate"] = 48_000

    with root_config_path.open("w", encoding="utf-8") as file:
        json.dump(root_config, file, indent=2, ensure_ascii=False)
        file.write("\n")

    print(f"Created 48 kHz model at: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
