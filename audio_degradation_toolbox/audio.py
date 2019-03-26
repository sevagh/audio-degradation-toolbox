import numpy
import array
from pydub import AudioSegment
from pydub.utils import get_array_type


class Audio(object):
    def __init__(self, path=None, ext=None, samples=None, old_faudio=None):
        if path and (samples is not None):
            raise ValueError("Only pass one of path[+ext] or raw[+old_faudio]")

        if path:
            if not ext:
                ext = path.split(".")[-1]
            self.sound = AudioSegment.from_file(file=path, format=ext).set_channels(1)
            self.samples = self.sound.get_array_of_samples()
            self.sample_rate = self.sound.frame_rate
            self.format = ext
            self.dtype = get_array_type(self.sound.sample_width * 8)
        if samples is not None:
            self.samples = samples
            self.sample_rate = old_faudio.sample_rate
            self.sound = old_faudio.sound._spawn(self.samples)
            self.format = old_faudio.format
            self.dtype = old_faudio.dtype

    def export(self, path):
        self.sound.export(out_f=path, format="wav")
