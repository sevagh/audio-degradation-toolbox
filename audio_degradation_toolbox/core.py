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
    mp3_transcode,
    apply_gain,
    apply_normalization,
    apply_highpass,
    apply_lowpass,
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
