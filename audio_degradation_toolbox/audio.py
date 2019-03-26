import numpy
from pydub import AudioSegment
from pydub.utils import get_array_type


class Audio(object):
    def __init__(self, path=None, ext=None, raw=None, old_faudio=None):
        if path and (raw is not None):
            raise ValueError("Only pass one of path[+ext] or raw[+old_faudio]")

        if path:
            if not ext:
                ext = path.split(".")[-1]
            self.sound = AudioSegment.from_file(file=path, format=ext).set_channels(1)

            #self.dtype = get_array_type(self.sound.sample_width * 8)
            self.raw = numpy.frombuffer(self.sound._data, dtype=numpy.float64)
            self.sample_rate = self.sound.frame_rate
            self.format = ext
        if raw is not None:
            self.dtype = raw.dtype
            self.raw = raw
            self.sample_rate = old_faudio.sample_rate
            self.sound = AudioSegment(
                self.raw,
                frame_rate=self.sample_rate,
                sample_width=old_faudio.sound.sample_width,
                channels=1,
            )
            self.format = old_faudio.format

    def export(self, path):
        export_sound = AudioSegment(
            self.raw,
            frame_rate=self.sample_rate,
            sample_width=self.sound.sample_width,
            channels=1,
        )
        export_sound.export(out_f=path, format="wav")
