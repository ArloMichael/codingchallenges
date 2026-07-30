import numpy as np
from mlx_audio.tts.utils import load_model
from mlx_audio.utils import load_audio

def patch_qwen3_conv_layout():
    from mlx_audio.tts.models.qwen3_tts import qwen3_tts

    original = qwen3_tts.check_array_shape_qwen3

    if getattr(original, "_qwen_48k_patched", False):
        return

    def fixed(array):
        shape = array.shape

        if len(shape) == 3:
            output_channels, second, third = shape

            if second == 1 and third == output_channels:
                return True

            if third == 1 and second == output_channels:
                return False

        return original(array)

    fixed._qwen_48k_patched = True
    qwen3_tts.check_array_shape_qwen3 = fixed


def load_tts_model(model_path):
    patch_qwen3_conv_layout()
    return load_model(str(model_path))


def load_reference_audio(reference_audio_path):
    return load_audio(
        reference_audio_path,
        sample_rate=24_000,
        volume_normalize=False,
    )


def load_default_tts(
    model_path,
    reference_audio_path,
):
    model = load_tts_model(model_path)
    reference_audio = load_reference_audio(reference_audio_path)
    return model, reference_audio


def stream_tts_results(
    model,
    reference_audio,
    *,
    text,
    ref_text,
    voice=None,
    lang_code="English",
    streaming_interval=0.8,
    temperature=0.7,
    top_p=0.9,
    top_k=50,
    repetition_penalty=1.1,
    max_tokens=1200,
    verbose=False,
):
    yield from model.generate(
        voice=voice,
        stream=True,
        streaming_interval=streaming_interval,
        text=text,
        ref_audio=reference_audio,
        ref_text=ref_text,
        lang_code=lang_code,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        repetition_penalty=repetition_penalty,
        max_tokens=max_tokens,
        verbose=verbose,
    )


def stream_tts_float32_bytes(model, reference_audio, **kwargs):
    for result in stream_tts_results(model, reference_audio, **kwargs):
        audio = np.asarray(result.audio, dtype=np.float32)
        audio = np.clip(audio, -1.0, 1.0)
        yield audio.tobytes()
