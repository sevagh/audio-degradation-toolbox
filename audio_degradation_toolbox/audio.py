import numpy
import array
from pydub import AudioSegment
from pydub.utils import get_array_type


class Audio(object):
    def __init__(
        self,
        path=None,
        ext=None,
        samples=None,
        old_audio=None,
        sound=None,
        sample_rate=None,
    ):
        if (
            (path and (samples is not None))
            or (path and sound)
            or (sound and (samples is not None))
        ):
            raise ValueError(
                "Only pass one of path[+ext] or samples[+old_audio] or sound[+old_audio]"
            )

        if path:
            if not ext:
                ext = path.split(".")[-1]
            self.sound = AudioSegment.from_file(file=path, format=ext).set_channels(1)
            self.samples = self.sound.get_array_of_samples()
            self.sample_rate = self.sound.frame_rate
            self.format = ext
        if samples is not None:
            self.samples = samples
            if sample_rate:
                self.sample_rate = sample_rate
            else:
                self.sample_rate = old_audio.sample_rate
            self.sample_rate = int(self.sample_rate)
            self.sound = AudioSegment(
                data=self.samples,
                sample_width=old_audio.sound.sample_width,
                frame_rate=self.sample_rate,
                channels=1,
            )
            self.format = old_audio.format
        if sound:
            self.sound = sound
            self.samples = self.sound.get_array_of_samples()
            self.sample_rate = sound.frame_rate
            self.format = old_audio.format

    def export(self, path):
        self.sound.export(out_f=path, format="wav")
