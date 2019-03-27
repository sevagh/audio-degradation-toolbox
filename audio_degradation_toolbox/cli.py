from .core import Degradation
from .playback import playback_shim
import argparse
import json

INTRO = """
Apply controlled degradations to an audio file

Available degradations (executed in order of the JSON array):

    noise: add noise to produce desired SNR
    {
        "name": "noise",
        ["snr": 20,]
        ["color": "violet"]
    }

    mp3: transcode file to mp3 with given bitrate
    {
        "name": "mp3",
        ["bitrate": 320]
    }

    gain: add volume in db
    {
        "name": "gain",
        ["volume": 10]
    }

    normalize
    {
        "name": "normalize"
    }

    low_pass: apply a low-pass filter
    {
        "name": "low_pass",
        ["cutoff": 1000]
    }

    high_pass: apply a high-pass filter
    {
        "name": "high_pass",
        ["cutoff": 1000]
    }

    trim_millis: lop off milliseconds at offset (-1 = from end)
    {
        "name": "trim_millis",
        ["amount": 100,]
        ["offset": 0]
    }

    mix: mix another audio file with the original
    {
        "name": "mix",
        "path": "./relative_path_mix.wav"
    }

    impulse_response: convolve with IR
    {
        "name": "impulse_response",
        "path": "./relative_path_ir.wav"
    }

    speedup: make it faster
    {
        "name": "speedup",
        "speed": 2
    }

    resample: resample to new sampling rate
    {
        "name": "resample",
        "rate": 44100
    }

    pitch_shift
    {
        "name": "pitch_shift",
        "ocatves": -0.5
    }

    dynamic_range_compression
    {
        "name": "dynamic_range_compression",
        ["threshold": -20,]
        ["ratio": 4.0,]
        ["attack": 5.0,]
        ["release": 50.0]
    }
"""


def main():
    parser = argparse.ArgumentParser(
        prog="audio-degradation-toolbox",
        description=INTRO,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-d", "--degradations-file", help="JSON file of degradations to apply"
    )
    parser.add_argument(
        "-p",
        "--play",
        action="store_true",
        help="Play file audio at each degradation step",
    )
    parser.add_argument(
        "-t", "--trim", action="store_true", help="Trim trailing and leading silences"
    )
    parser.add_argument("input_path", help="Path to input file")
    parser.add_argument("output_path", help="Path to output WAV file")
    args = parser.parse_args()

    deg = Degradation(path=args.input_path, trim_on_load=args.trim)

    if args.degradations_file:
        with open(args.degradations_file) as f:
            degradations = json.load(f)

            if args.play:
                print("Playing audio before degradations")
                playback_shim(deg.file_audio)

            for degradation in degradations:
                deg.apply_degradation(degradation, play_=args.play)

    deg.file_audio.export(args.output_path)
