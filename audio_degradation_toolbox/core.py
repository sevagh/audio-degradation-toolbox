import numpy
from pydub import AudioSegment
from pydub.utils import get_array_type
from pydub.playback import play
from .degradations import apply_noise
from acoustics import Signal


def print_hello():
    print("Hello, World!")


class FileAudio(object):
    def __init__(self, path):
        ext = path.split(".")[-1]
        self.sound = AudioSegment.from_file(file=path, format=ext).set_channels(1)

        self.raw = numpy.frombuffer(
            self.sound._data, dtype=get_array_type(self.sound.sample_width * 8)
        )
        self.raw_len = len(self.raw)
        self.sample_rate = self.sound.frame_rate
        self.format = ext

    def apply_degradation(self, d):
        degradation = [d_.strip() for d_ in d.split(",")]
        if len(degradation) == 0:
            raise ValueError("Degradations must be in the format name,param,param,...")

        name = degradation[0]
        if name == "noise":
            color = None
            snr = None
            try:
                color = degradation[1]
                snr = float(degradation[2])
            except Exception:
                pass
            self.raw = apply_noise(self, color=color, SNR=snr)

        self.sound = AudioSegment(
            self.raw,
            frame_rate=self.sample_rate,
            sample_width=self.sound.sample_width,
            channels=1,
        )

    def export(self, path):
        self.sound.export(out_f=path, format="wav")
