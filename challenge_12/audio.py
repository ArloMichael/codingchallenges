import numpy as np
import pygame

from settings import (
    MUSIC_ENABLED,
    MUSIC_PATH,
    MUSIC_VOLUME,
    SFX_ENABLED,
    SFX_PATHS,
    SFX_REVERB_ALLPASS_DELAYS_MS,
    SFX_REVERB_ALLPASS_FEEDBACK,
    SFX_REVERB_CHANNELS,
    SFX_REVERB_COMB_DELAYS_MS,
    SFX_REVERB_DAMPING,
    SFX_REVERB_DECAY_SECONDS,
    SFX_REVERB_DRY,
    SFX_REVERB_DURATION_SECONDS,
    SFX_REVERB_ENABLED,
    SFX_REVERB_PREDELAY_MS,
    SFX_REVERB_STEREO_SPREAD,
    SFX_REVERB_WET,
    SFX_VOLUME,
)


class Audio:
    """Own the application's continuous music and reusable sound effects."""

    def __init__(self):
        self.available = pygame.mixer.get_init() is not None
        self.music_enabled = MUSIC_ENABLED
        self.sfx_enabled = SFX_ENABLED
        self.sounds = {}

        if not self.available:
            return

        sample_rate, sample_format, channels = pygame.mixer.get_init()
        pygame.mixer.set_num_channels(SFX_REVERB_CHANNELS)
        pygame.mixer.music.set_volume(MUSIC_VOLUME)
        self.reverb_ir = None
        if SFX_REVERB_ENABLED and abs(sample_format) == 16:
            # Build the room response once, then reuse it for every loaded effect.
            self.reverb_ir = self._make_schroeder_ir(sample_rate, channels)

        self.sounds = {
            name: self._load_sfx(path)
            for name, path in SFX_PATHS.items()
            if path.is_file()
        }
        self.set_sfx_volume(SFX_VOLUME)

    def start_music(self):
        if (
            not self.available
            or not self.music_enabled
            or pygame.mixer.music.get_busy()
        ):
            return

        try:
            pygame.mixer.music.load(MUSIC_PATH)
            pygame.mixer.music.play(loops=-1)
        except (FileNotFoundError, pygame.error):
            self.music_enabled = False

    def play(self, name):
        if not self.available or not self.sfx_enabled:
            return

        sound = self.sounds.get(name)
        if sound:
            sound.play()

    def set_sfx_volume(self, volume):
        for sound in self.sounds.values():
            sound.set_volume(volume)

    def close(self):
        if self.available:
            pygame.mixer.music.stop()
            pygame.mixer.stop()

    def _load_sfx(self, path):
        sound = pygame.mixer.Sound(path)
        if self.reverb_ir is None:
            return sound

        return self._apply_reverb(sound)

    def _apply_reverb(self, sound):
        dry_samples = pygame.sndarray.array(sound)
        was_mono = dry_samples.ndim == 1
        if was_mono:
            dry_samples = dry_samples[:, np.newaxis]

        dry = dry_samples.astype(np.float32) / 32768
        output_length = len(dry) + len(self.reverb_ir) - 1
        fft_length = 1 << (output_length - 1).bit_length()
        mixed = np.zeros((output_length, dry.shape[1]), dtype=np.float32)

        for channel in range(dry.shape[1]):
            ir_channel = min(channel, self.reverb_ir.shape[1] - 1)
            wet = np.fft.irfft(
                np.fft.rfft(dry[:, channel], fft_length)
                * np.fft.rfft(self.reverb_ir[:, ir_channel], fft_length),
                fft_length,
            )[:output_length]
            mixed[:, channel] = wet * SFX_REVERB_WET

        mixed[:len(dry)] += dry * SFX_REVERB_DRY
        np.clip(mixed, -1, 1, out=mixed)

        if was_mono:
            mixed = mixed[:, 0]

        samples = np.ascontiguousarray((mixed * 32767).astype(np.int16))
        return pygame.sndarray.make_sound(samples)

    def _make_schroeder_ir(self, sample_rate, channels):
        frame_count = int(sample_rate * SFX_REVERB_DURATION_SECONDS)
        predelay = int(sample_rate * SFX_REVERB_PREDELAY_MS / 1000)
        impulse = np.zeros(frame_count, dtype=np.float32)
        impulse[min(predelay, frame_count - 1)] = 1
        impulse_response = np.zeros((frame_count, channels), dtype=np.float32)

        for channel in range(channels):
            spread = 1 + (
                channel - (channels - 1) / 2
            ) * SFX_REVERB_STEREO_SPREAD
            combined = np.zeros(frame_count, dtype=np.float32)

            for delay_ms in SFX_REVERB_COMB_DELAYS_MS:
                delay = max(1, int(sample_rate * delay_ms * spread / 1000))
                delay_seconds = delay / sample_rate
                feedback = 10 ** (
                    -3 * delay_seconds / SFX_REVERB_DECAY_SECONDS
                )
                combined += self._feedback_comb(
                    impulse,
                    delay,
                    feedback,
                    SFX_REVERB_DAMPING,
                )

            combined /= len(SFX_REVERB_COMB_DELAYS_MS)
            for delay_ms in SFX_REVERB_ALLPASS_DELAYS_MS:
                delay = max(1, int(sample_rate * delay_ms * spread / 1000))
                combined = self._allpass(
                    combined,
                    delay,
                    SFX_REVERB_ALLPASS_FEEDBACK,
                )

            energy = np.sqrt(np.sum(combined * combined))
            if energy > 0:
                combined /= energy

            impulse_response[:, channel] = combined

        return impulse_response

    def _feedback_comb(self, signal, delay, feedback, damping):
        output = np.zeros_like(signal)
        buffer = np.zeros(delay, dtype=np.float32)
        buffer_index = 0
        filter_state = 0

        for index, sample in enumerate(signal):
            delayed = buffer[buffer_index]
            filter_state = delayed * (1 - damping) + filter_state * damping
            buffer[buffer_index] = sample + filter_state * feedback
            output[index] = delayed
            buffer_index = (buffer_index + 1) % delay

        return output

    def _allpass(self, signal, delay, feedback):
        output = np.zeros_like(signal)
        buffer = np.zeros(delay, dtype=np.float32)
        buffer_index = 0

        for index, sample in enumerate(signal):
            delayed = buffer[buffer_index]
            output[index] = delayed - sample
            buffer[buffer_index] = sample + delayed * feedback
            buffer_index = (buffer_index + 1) % delay

        return output
