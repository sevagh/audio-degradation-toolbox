import numpy
from pydub import AudioSegment
from pydub.utils import get_array_type
from pydub.playback import play
from acoustics import Signal
from acoustics.generator import noise
import math
from tempfile import NamedTemporaryFile
from .audio import Audio
import array


def apply_noise(audio, color, snr):
    Ps = Signal(audio.samples, audio.sample_rate).power()
    noise_data = noise(len(audio.samples), color=color)
    Pn = Signal(noise_data, audio.sample_rate).power()
    noise_data *= math.sqrt((Ps / Pn) * (10 ** (-snr / 10)))
    noise_data = array.array(audio.sound.array_type, noise_data.astype(int))

    # for i in range(100):
    #    print(noise_data[i*100:(i+1)*100])
    #    input()

    a_ = Audio(samples=noise_data, old_faudio=audio)
    play(a_.sound)
    for i in range(len(noise_data)):
        noise_data[i] += audio.samples[i]
    a = Audio(samples=noise_data, old_faudio=audio)
    play(a.sound)
    return a_


def mp3_transcode(audio, bitrate):
    # do a pydub round trip through an mp3 file
    with NamedTemporaryFile() as tmp_mp3_f:
        audio.sound.export(
            out_f=tmp_mp3_f.name, format="mp3", bitrate="{0}k".format(bitrate)
        )
        return Audio(path=tmp_mp3_f, ext="mp3")
