from acoustics.generator import noise
from acoustics import Signal
import math


def apply_noise(audio, color="pink", SNR=20):
    Ps = Signal(audio.raw, audio.sample_rate).power()

    noise_data = noise(audio.raw_len, color=color)
    Pn = Signal(noise_data, audio.sample_rate).power()

    noise_data *= math.sqrt((Ps / Pn) * (10 ** (-SNR / 10)))

    orig_dtype = audio.raw.dtype
    return (audio.raw + noise_data).astype(orig_dtype)
