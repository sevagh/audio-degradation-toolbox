import numpy
from pydub import AudioSegment
from pydub.utils import get_array_type
from pydub.playback import play
from acoustics import Signal
from acoustics.generator import noise
import math
from tempfile import NamedTemporaryFile
from .degradations import apply_noise, mp3_transcode
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
        else:
            raise ValueError("Invalid degradation {0}".format(name))

        print("Applied degradation {0} with params {1}".format(name, params))
        if play_:
            print("Playing audio after degradation")
            play(self.file_audio.sound)
