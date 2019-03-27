from tempfile import NamedTemporaryFile
import subprocess


def playback_shim(audio):
    with NamedTemporaryFile() as audio_f:
        audio.export(audio_f.name)
        subprocess.check_output("mpv {0}".format(audio_f.name), shell=True)
