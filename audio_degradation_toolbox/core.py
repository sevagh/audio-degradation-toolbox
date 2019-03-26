import numpy
from pydub import AudioSegment
from pydub.utils import get_array_type
from .playback import playback_shim
from acoustics import Signal
from acoustics.generator import noise
import math
from tempfile import NamedTemporaryFile
from .degradations import (
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
)
from .audio import Audio


class Degradation(object):
    def __init__(self, path, ext=None):
        self.file_audio = Audio(path, ext=ext)

    def apply_degradation(self, d, play_):
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
            self.file_audio = apply_lowpass(self.file_audio, cutoff)
            params = "cutoff: {0}".format(cutoff)
        elif name == "high_pass":
            cutoff = float(d.get("cutoff", 1000.0))
            self.file_audio = apply_highpass(self.file_audio, cutoff)
            params = "cutoff: {0}".format(cutoff)
        elif name == "trim_millis":
            amount = int(d.get("amount", 100))
            offset = int(d.get("offset", 0))
            self.file_audio = trim_millis(self.file_audio, amount, offset)
            params = "amount: {0}, offset: {1}".format(amount, offset)
        elif name == "mix":
            mix_path = d["path"]
            snr = d.get("snr", 20)
            self.file_audio = apply_mix(self.file_audio, mix_path, snr)
            params = "mix_path: {0}, snr: {1}".format(mix_path, snr)
        elif name == "speedup":
            speed = d["speed"]
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
