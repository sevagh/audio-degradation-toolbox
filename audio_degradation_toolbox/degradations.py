import numpy
from numpy.linalg import norm
from pydub import AudioSegment
from pydub.utils import get_array_type
import pydub.effects as pydub_effects
from acoustics.generator import noise
import math
from tempfile import NamedTemporaryFile
from .audio import Audio
from .playback import playback_shim
import array
import sys
import scipy.signal as scipy_signal


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


def apply_low_pass(audio, cutoff):
    return Audio(
        sound=pydub_effects.low_pass_filter(audio.sound, cutoff), old_audio=audio
    )


def apply_high_pass(audio, cutoff):
    return Audio(
        sound=pydub_effects.high_pass_filter(audio.sound, cutoff), old_audio=audio
    )


def trim_millis(audio, amount, offset):
    if amount >= len(audio.sound):
        print(
            "Not trimming amount {0} longer than file {1}".format(
                amount, len(audio.sound)
            ),
            file=sys.stderr,
        )
        return audio

    ret = None
    if offset == -1:
        ret = Audio(sound=audio.sound[: len(audio.sound) - amount], old_audio=audio)
    else:
        ret = Audio(
            sound=(audio.sound[: offset + 1] + audio.sound[offset + amount + 1 :]),
            old_audio=audio,
        )

    print("New length: {0}".format(len(ret.sound)))
    return ret


def _mix(audio, mix_data, snr):
    Ps = 0
    Pn = 0

    for i in range(len(audio.samples)):
        Ps += abs(audio.samples[i]) * abs(audio.samples[i])
        Pn += abs(mix_data[i]) * abs(mix_data[i])
    Ps /= len(audio.samples)
    Pn /= len(audio.samples)

    k_factor = math.sqrt((Ps / Pn) * (10 ** (-snr / 10)))
    mix_data *= k_factor

    # some necessary casting to avoid fucking with the length of the audio file
    mix_data = array.array(
        audio.sound.array_type, mix_data.astype(audio.sound.array_type)
    )

    for i in range(len(mix_data)):
        try:
            mix_data[i] += audio.samples[i]
        except OverflowError:
            try:
                mix_data[i] = numpy.finfo(mix_data.typecode).max
            except ValueError:
                mix_data[i] = numpy.iinfo(mix_data.typecode).max
    a = Audio(samples=mix_data, old_audio=audio)
    return a


def _stretch_mix(audio, mix_audio):
    if len(mix_audio.samples) > len(audio.samples):
        mix_audio = Audio(
            samples=mix_audio.samples[: len(audio.samples)], old_audio=mix_audio
        )
    elif len(mix_audio.samples) < len(audio.samples):
        m_s = mix_audio.samples
        while len(m_s) < len(audio.samples):
            m_s += m_s[
                : min(
                    len(audio.samples) - len(mix_audio.samples), len(mix_audio.samples)
                )
            ]
        mix_audio = Audio(samples=m_s, old_audio=mix_audio)

    return mix_audio


def apply_mix(audio, mix, snr):
    mix_audio = Audio(path=mix)
    mix_audio = _stretch_mix(audio, mix_audio)
    mix_data = numpy.frombuffer(mix_audio.samples, dtype=mix_audio.sound.array_type)

    mix_audio = Audio(samples=mix_data, old_audio=mix_audio)

    mix_data = numpy.frombuffer(
        mix_audio.samples, dtype=mix_audio.sound.array_type
    ).astype(numpy.float64)
    return _mix(audio, mix_data, snr)


def apply_noise(audio, color, snr):
    noise_data = noise(len(audio.samples), color=color)
    return _mix(audio, noise_data, snr)


def apply_speedup(audio, speed):
    return Audio(sound=pydub_effects.speedup(audio.sound, speed), old_audio=audio)


def apply_resample(audio, new_sample_rate):
    return Audio(sound=audio.sound.set_frame_rate(new_sample_rate), old_audio=audio)


def apply_pitch_shift(audio, octaves):
    new_sample_rate = int(audio.sample_rate * (2.0 ** octaves))
    return apply_resample(audio, new_sample_rate)


def apply_dynamic_range_compression(audio, threshold, ratio, attack, release):
    return Audio(
        sound=pydub_effects.compress_dynamic_range(
            audio.sound, threshold, ratio, attack, release
        ),
        old_audio=audio,
    )


# thanks https://github.com/limmor1/Convolve
def _normalize(y, bitwidth):
    if abs(numpy.amax(y)) > abs(numpy.amin(y)):
        larger = numpy.amax(y)
    else:
        larger = abs(numpy.amin(y))
    y = y / larger * ((2 ** bitwidth / 2) - 1)
    return y


def apply_impulse_response(audio, ir_path):
    ir = Audio(path=ir_path)

    if ir.sample_rate != audio.sample_rate:
        ir = apply_resample(ir, audio.sample_rate)

    conv_s = scipy_signal.fftconvolve(audio.samples, ir.samples)
    conv_s = _normalize(conv_s, audio.sound.sample_width * 8)

    conv_s = array.array(audio.sound.array_type, conv_s.astype(audio.sound.array_type))

    conv = Audio(samples=conv_s, old_audio=audio)
    return conv
