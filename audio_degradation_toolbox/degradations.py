import numpy
import pydub.effects as pydub_effects
import pydub.scipy_effects
from acoustics.generator import noise
import math
from tempfile import NamedTemporaryFile
from .audio import Audio
import array
import sys
import scipy.signal as scipy_signal
import scipy.interpolate as scipy_interpolate
import librosa
import numba
from pysndfx import AudioEffectsChain


def mp3_transcode(audio, bitrate):
    # do a pydub round trip through an mp3 file
    ret = None
    with NamedTemporaryFile() as tmp_mp3_f:
        audio.sound.export(
            out_f=tmp_mp3_f.name, format="mp3", bitrate="{0}k".format(bitrate)
        )
        ret = Audio(path=tmp_mp3_f, ext="mp3")
    return ret


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
    return apply_resample(audio, audio.sample_rate / speed)


def apply_resample(audio, new_sample_rate):
    int_sample_rate = int(new_sample_rate)
    return Audio(sound=audio.sound.set_frame_rate(int_sample_rate), old_audio=audio)


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


def apply_impulse_response(audio, ir_path):
    ir = Audio(path=ir_path)

    if ir.sample_rate != audio.sample_rate:
        ir = apply_resample(ir, audio.sample_rate)

    conv_s = scipy_signal.fftconvolve(audio.samples, ir.samples)
    conv_s = _normalize(conv_s, audio.sound.sample_width * 8)

    conv_s = array.array(audio.sound.array_type, conv_s.astype(audio.sound.array_type))

    conv = Audio(samples=conv_s, old_audio=audio)
    return conv


def apply_time_stretch(audio, factor):
    samples = numpy.frombuffer(audio.samples, dtype=audio.sound.array_type).astype(
        numpy.float64
    )
    stretched = librosa.effects.time_stretch(samples, factor)
    stretched = _normalize(stretched, audio.sound.sample_width * 8)

    return Audio(
        samples=array.array(
            audio.sound.array_type, stretched.astype(audio.sound.array_type)
        ),
        old_audio=audio,
    )


def trim(audio):
    samples = numpy.frombuffer(audio.samples, dtype=audio.sound.array_type).astype(
        numpy.float64
    )
    trimmed, _ = librosa.effects.trim(samples)
    trimmed = _normalize(trimmed, audio.sound.sample_width * 8)

    return Audio(
        samples=array.array(
            audio.sound.array_type, trimmed.astype(audio.sound.array_type)
        ),
        old_audio=audio,
    )


def apply_eq(audio, frequency, q, db):
    fx = AudioEffectsChain().equalizer(frequency, q, db)

    samples = numpy.frombuffer(audio.samples, dtype=audio.sound.array_type).astype(
        numpy.float64
    )

    samples = fx(samples)
    samples = _normalize(samples, audio.sound.sample_width * 8)

    return Audio(
        samples=array.array(
            audio.sound.array_type, samples.astype(audio.sound.array_type)
        ),
        old_audio=audio,
    )


def apply_delay(audio, n_samples):
    samples = (
        array.array(audio.sound.array_type, [0 for _ in range(n_samples)])
        + audio.samples
    )
    return Audio(samples=samples, old_audio=audio)


def apply_clipping(audio, n_samples, percent_samples):
    if n_samples != 0 and percent_samples != 0.0:
        raise ValueError("only specify one of samples or percent_samples")

    def db2mag(ydb):
        y = math.pow(10, ydb / 20)
        return y

    eps = numpy.spacing(1)

    samples = numpy.frombuffer(audio.samples, dtype=audio.sound.array_type).astype(
        numpy.complex
    )

    if n_samples == 0 and percent_samples == 0.0:
        quant_measured = max(
            numpy.quantile(numpy.mean(numpy.power(samples, 2.2)), 0.95), eps
        )
        quant_wanted = db2mag(-5)
        samples_out = samples * (quant_wanted / quant_measured)
    else:
        sorted_samples = numpy.abs(samples)
        sorted_samples.sort()
        num_samples = len(sorted_samples)
        if n_samples == 0:
            n_samples = int(percent_samples * num_samples)
        divisor = numpy.min(sorted_samples[num_samples - n_samples + 1 : num_samples])
        divisor = max(divisor, eps)
        samples_out = samples / divisor

    samples_out = numpy.clip(samples_out, -1, 1)
    samples_out *= 0.99

    samples_out = _normalize(samples_out, audio.sound.sample_width * 8)

    return Audio(
        samples=array.array(
            audio.sound.array_type, samples_out.astype(audio.sound.array_type)
        ),
        old_audio=audio,
    )


# straight from matlab
def apply_wow_flutter(audio, intensity, frequency, upsampling_factor):
    audio_out = audio.samples

    fs_oversampled = audio.sample_rate * upsampling_factor
    a_m = intensity / 100.0
    f_m = frequency

    num_samples = len(audio.samples)
    len_secs = len(audio.sound) / 1000.0
    num_full_periods = math.floor(len_secs * f_m)
    num_samples_to_warp = numpy.round(num_full_periods * audio.sample_rate / f_m)

    old_sample_positions_to_new_oversampled_positions = numpy.round(
        _time_assignment_new_to_old(
            numpy.arange(1, num_samples_to_warp) / audio.sample_rate, a_m, f_m
        )
        * fs_oversampled
    )

    audio_upsampled = apply_resample(audio, fs_oversampled).samples

    for i, pos in enumerate(old_sample_positions_to_new_oversampled_positions):
        audio_out[1 + i] = audio_upsampled[int(numpy.round(pos))]

    return Audio(samples=audio_out, sample_rate=fs_oversampled, old_audio=audio)


# from matlab
@numba.jit
def apply_aliasing(audio, dest_frequency):
    n_samples = len(audio.samples)
    n_samples_new = int(numpy.round(n_samples / audio.sample_rate * dest_frequency))
    t_old = numpy.arange(0.0, n_samples) / audio.sample_rate
    t_new = numpy.arange(0.0, n_samples_new) / dest_frequency

    audio_samples = numpy.frombuffer(
        audio.samples, dtype=audio.sound.array_type
    ).astype(numpy.float64)

    interp = scipy_interpolate.interp1d(t_old, audio_samples, kind="nearest")
    tmp = numpy.asarray([interp(t_new[x]) for x in range(len(t_new))], dtype=numpy.int)

    tmp_audio = Audio(
        samples=array.array(audio.sound.array_type, tmp),
        old_audio=audio,
        sample_rate=dest_frequency,
    )
    return apply_resample(tmp_audio, audio.sample_rate)


#quadratic distortion, approximated with sine (chebyshev polynomials?)
@numba.jit
def apply_harmonic_distortion(audio, num_passes):
    audio_samples = numpy.frombuffer(
        audio.samples, dtype=audio.sound.array_type
    ).astype(numpy.float64)

    # normalize to between -1 and 1
    a_min = audio_samples.min()
    a_max = audio_samples.max()

    audio_samples = numpy.interp(audio_samples, (a_min, a_max), (-1.0, +1.0))

    for _ in range(num_passes):
        audio_samples = numpy.sin(audio_samples * (math.pi / 2.0))

    # scale it back up?
    audio_samples = numpy.interp(audio_samples, (-1.0, +1.0), (a_min, a_max))

    return Audio(
        samples=array.array(audio.sound.array_type, audio_samples.astype(numpy.int)),
        old_audio=audio,
    )


def trim(audio):
    samples = numpy.frombuffer(audio.samples, dtype=audio.sound.array_type).astype(
        numpy.float64
    )
    trimmed, _ = librosa.effects.trim(samples)
    trimmed = _normalize(trimmed, audio.sound.sample_width * 8)

    return Audio(
        samples=array.array(
            audio.sound.array_type, trimmed.astype(audio.sound.array_type)
        ),
        old_audio=audio,
    )


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


# thanks https://github.com/limmor1/Convolve
def _normalize(y, bitwidth):
    if abs(numpy.amax(y)) > abs(numpy.amin(y)):
        larger = numpy.amax(y)
    else:
        larger = abs(numpy.amin(y))
    y = y / larger * ((2 ** bitwidth / 2) - 1)
    return y


# copied straight from matlab
@numba.jit
def _times_assignment_old_to_new(x, a_m, f_m):
    time_assigned = [0.0 for _ in len(x)]

    for i, elem in enumerate(x):
        time_assigned[i] = (
            x[i] + a_m + math.sin(2.0 * math.pi * f_m * x[i]) / (2.0 * math.pi * f_m)
        )

    return numpy.ndarray(time_assigned)


@numba.jit
def _time_assignment_new_to_old(y, a_m, f_m):
    time_assigned = y

    for k in range(1, 41):
        for i, elem in enumerate(y):
            time_assigned[i] = y[i] - a_m * math.sin(
                2.0 * math.pi * f_m * time_assigned[i]
            ) / (2.0 * math.pi * f_m)

    return time_assigned
