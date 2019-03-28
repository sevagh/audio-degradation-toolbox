from .core import Degradation
from .playback import playback_shim
import argparse
import json

INTRO = """
Apply controlled degradations to an audio file, specified in a JSON file containing an array of degradations (executed in order).

Paths are relative to the execution dir, and square brackets denote optional arguments along with their default values.

    { "name": "noise", ["snr": 20, "color": "pink"] }
    { "name": "mp3", ["bitrate": 320] }
    { "name": "gain", ["volume": 10.0] }
    { "name": "normalize" }
    { "name": "low_pass", ["cutoff": 1000.0] }
    { "name": "high_pass", ["cutoff": 1000.0] }
    { "name": "trim_millis", ["amount": 100, "offset": 0] }
    { "name": "mix", "path": STRING, ["snr": 20.0] }
    { "name": "speedup", "speed": FLOAT }
    { "name": "resample", "rate": INT }
    { "name": "pitch_shift", "octaves": FLOAT }
    { "name": "dynamic_range_compression", ["threshold": -20.0, "ratio": 4.0, "attack": 5.0, "release": 50.0] }
    { "name": "impulse_response", "path": STRING }
    { "name": "equalizer", "frequency": FLOAT, ["bandwidth": 1.0, "gain": -3.0] }
    { "name": "time_stretch", "factor": FLOAT }
    { "name": "delay", "samples": INT }
    { "name": "clipping", ["samples": 0, "percent_samples": 0.0] }
    { "name": "wow_flutter", ["intensity": 1.5, "frequency": 0.5, "upsampling_factor": 5.0 ] }
    { "name": "aliasing", ["dest_frequency": 8000.0] }
    { "name": "harmonic_distortion", ["num_passes": 3] }
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
