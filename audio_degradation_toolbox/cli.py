from .core import Degradation
import argparse
import json
from pydub.playback import play

INTRO = """
Apply controlled degradations to an audio file

Available degradations:
    Noise: add noise to produce desired SNR
    {
        "name": "noise",
        ["snr": 20,]
        ["color": "violet"]
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
    parser.add_argument("input_path", help="Path to input file")
    parser.add_argument("output_path", help="Path to output WAV file")
    args = parser.parse_args()

    deg = Degradation(path=args.input_path)

    if args.play:
        print("Playing audio before degradations")
        play(deg.file_audio.sound)

    if args.degradations_file:
        with open(args.degradations_file) as f:
            degradations = json.load(f)
            for degradation in degradations:
                deg.apply_degradation(degradation, play_=args.play)

    deg.file_audio.export(args.output_path)
