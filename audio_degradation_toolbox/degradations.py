import numpy
from pydub import AudioSegment
from pydub.utils import get_array_type
from pydub.playback import play
import pydub.effects as pydub_effects
from acoustics.generator import noise
import math
from tempfile import NamedTemporaryFile
from .audio import Audio
import array


def apply_noise(audio, color, snr):
    noise_data = noise(len(audio.samples), color=color)

    Ps = 0
    Pn = 0

    for i in range(len(audio.samples)):
        Ps += abs(audio.samples[i]) * abs(audio.samples[i])
        Pn += abs(noise_data[i]) * abs(noise_data[i])
    Ps /= len(audio.samples)
    Pn /= len(audio.samples)

    k_factor = math.sqrt((Ps / Pn) * (10 ** (-snr / 10)))
    noise_data *= k_factor

    noise_data = array.array(audio.sound.array_type, noise_data.astype(int))

    for i in range(len(noise_data)):
        noise_data[i] += audio.samples[i]
    a = Audio(samples=noise_data, old_audio=audio)
    return a


def mp3_transcode(audio, bitrate):
    # do a pydub round trip through an mp3 file
    with NamedTemporaryFile() as tmp_mp3_f:
        audio.sound.export(
            out_f=tmp_mp3_f.name, format="mp3", bitrate="{0}k".format(bitrate)
        )
        return Audio(path=tmp_mp3_f, ext="mp3")


def apply_gain(audio, gain_dbs):
    return Audio(sound=audio.sound.apply_gain(gain_dbs), old_audio=audio)


def apply_normalization(audio):
    return Audio(sound=pydub_effects.normalize(audio.sound), old_audio=audio)


def apply_lowpass(audio, cutoff):
    return Audio(
        sound=pydub_effects.low_pass_filter(audio.sound, cutoff), old_audio=audio
    )


def apply_highpass(audio, cutoff):
    return Audio(
        sound=pydub_effects.high_pass_filter(audio.sound, cutoff), old_audio=audio
    )
