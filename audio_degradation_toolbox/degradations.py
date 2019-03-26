import numpy
from pydub import AudioSegment
from pydub.utils import get_array_type
from acoustics import Signal
from acoustics.generator import noise
import math
from tempfile import NamedTemporaryFile
from .audio import Audio


def apply_noise(audio, color, snr):
    Ps = Signal(audio.raw, audio.sample_rate).power()
    noise_data = noise(len(audio.raw), color=color)
    Pn = Signal(noise_data, audio.sample_rate).power()
    noise_data *= math.sqrt((Ps / Pn) * (10 ** (-snr / 10)))
    noise_data = noise_data.astype(numpy.float32)
    new_raw = audio.raw + noise_data
    return Audio(raw=new_raw, old_faudio=audio)


def mp3_transcode(audio, bitrate):
    # do a pydub round trip through an mp3 file
    with NamedTemporaryFile() as tmp_mp3_f:
        audio.sound.export(
            out_f=tmp_mp3_f.name, format="mp3", bitrate="{0}k".format(bitrate)
        )
        return Audio(path=tmp_mp3_f, ext="mp3")
