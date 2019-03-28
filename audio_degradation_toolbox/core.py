import numpy
from pydub import AudioSegment
from pydub.utils import get_array_type
from .playback import playback_shim
from acoustics import Signal
from acoustics.generator import noise
import math
from tempfile import NamedTemporaryFile
from .degradations import (
    trim,
    apply_noise,
    apply_mix,
    mp3_transcode,
    apply_gain,
    apply_normalization,
    apply_high_pass,
    apply_low_pass,
    trim_millis,
    apply_speedup,
    apply_resample,
    apply_pitch_shift,
    apply_dynamic_range_compression,
    apply_impulse_response,
    apply_time_stretch,
    apply_eq,
    apply_delay,
    apply_clipping,
    apply_wow_flutter,
    apply_aliasing,
    apply_harmonic_distortion,
)
from .audio import Audio


class Degradation(object):
    def __init__(self, path, ext=None, trim_on_load=False):
        self.file_audio = Audio(path, ext=ext)
        if trim_on_load:
            self.file_audio = trim(self.file_audio)

    def apply_degradation(self, d, play_=False):
        name = d["name"]
        params = ""

        if name == "noise":
            color = d.get("color", "pink")
            snr = d.get("snr", 20)
            params = "color: {0}, snr: {1}".format(color, snr)
            self.file_audio = apply_noise(self.file_audio, color, snr)
        elif name == "mp3":
            bitrate = d.get("bitrate", 320)
            params = "bitrate: {0}".format(bitrate)
            self.file_audio = mp3_transcode(self.file_audio, bitrate)
        elif name == "gain":
            volume = float(d.get("volume", 10.0))
            self.file_audio = apply_gain(self.file_audio, volume)
            params = "volume: {0}".format(volume)
        elif name == "normalize":
            self.file_audio = apply_normalization(self.file_audio)
        elif name == "low_pass":
            cutoff = float(d.get("cutoff", 1000.0))
            self.file_audio = apply_low_pass(self.file_audio, cutoff)
            params = "cutoff: {0}".format(cutoff)
        elif name == "high_pass":
            cutoff = float(d.get("cutoff", 1000.0))
            self.file_audio = apply_high_pass(self.file_audio, cutoff)
            params = "cutoff: {0}".format(cutoff)
        elif name == "trim_millis":
            amount = int(d.get("amount", 100))
            offset = int(d.get("offset", 0))
            self.file_audio = trim_millis(self.file_audio, amount, offset)
            params = "amount: {0}, offset: {1}".format(amount, offset)
        elif name == "mix":
            mix_path = d["path"]
            snr = float(d.get("snr", 20.0))
            self.file_audio = apply_mix(self.file_audio, mix_path, snr)
            params = "mix_path: {0}, snr: {1}".format(mix_path, snr)
        elif name == "speedup":
            speed = float(d["speed"])
            self.file_audio = apply_speedup(self.file_audio, speed)
            params = "speed: {0}".format(speed)
        elif name == "resample":
            rate = int(d["rate"])
            self.file_audio = apply_resample(self.file_audio, rate)
            params = "rate: {0}".format(rate)
        elif name == "pitch_shift":
            octaves = float(d["octaves"])
            self.file_audio = apply_pitch_shift(self.file_audio, octaves)
            params = "octaves: {0}".format(octaves)
        elif name == "dynamic_range_compression":
            threshold = float(d.get("threshold", -20.0))
            ratio = float(d.get("ratio", 4.0))
            attack = float(d.get("attack", 5.0))
            release = float(d.get("release", 50.0))
            self.file_audio = apply_dynamic_range_compression(
                self.file_audio, threshold, ratio, attack, release
            )
            params = "threshold: {0}, ratio: {1}, attack: {2}, release: {3}".format(
                threshold, ratio, attack, release
            )
        elif name == "impulse_response":
            path = d["path"]
            self.file_audio = apply_impulse_response(self.file_audio, path)
            params = "path: {0}".format(path)
        elif name == "equalizer":
            frequency = float(d["frequency"])
            bandwidth = float(d.get("bandwidth", 1.0))
            gain = float(d.get("gain", -3.0))
            self.file_audio = apply_eq(self.file_audio, frequency, bandwidth, gain)
            params = "frequency: {0}, bandwidth: {1}, gain: {2}".format(
                frequency, bandwidth, gain
            )
        elif name == "time_stretch":
            factor = float(d["factor"])
            self.file_audio = apply_time_stretch(self.file_audio, factor)
            params = "factor: {0}".format(factor)
        elif name == "delay":
            n_samples = int(d["samples"])
            self.file_audio = apply_delay(self.file_audio, n_samples)
            params = "samples: {0}".format(n_samples)
        elif name == "clipping":
            n_samples = int(d.get("samples", 0))
            percent_samples = float(d.get("percent_samples", 0.0)) / 100.0
            self.file_audio = apply_clipping(
                self.file_audio, n_samples, percent_samples
            )
            params = "samples: {0}, percent_samples: {1}".format(
                n_samples, percent_samples
            )
        elif name == "wow_flutter":
            intensity = float(d.get("intensity", 1.5))
            frequency = float(d.get("frequency", 0.5))
            upsampling_factor = float(d.get("upsampling_factor", 5.0))
            self.file_audio = apply_wow_flutter(
                self.file_audio, intensity, frequency, upsampling_factor
            )
            params = "intensity: {0}, frequency: {1}, upsampling_factor: {2}".format(
                intensity, frequency, upsampling_factor
            )
        elif name == "aliasing":
            dest_frequency = float(d.get("dest_frequency", 8000.0))
            self.file_audio = apply_aliasing(self.file_audio, dest_frequency)
            params = "dest_frequency: {0}".format(dest_frequency)
        elif name == "harmonic_distortion":
            num_passes = int(d.get("num_passes", 3))
            self.file_audio = apply_harmonic_distortion(self.file_audio, num_passes)
            params = "num_passes: {0}".format(num_passes)
        else:
            raise ValueError("Invalid degradation {0}".format(name))

        print(
            "Applied degradation {0}{1}".format(
                name, " with params {0}".format(params) if params else ""
            )
        )
        if play_:
            print("Playing audio after degradation")
            playback_shim(self.file_audio)
