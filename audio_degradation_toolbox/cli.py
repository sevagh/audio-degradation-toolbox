from .core import FileAudio
import argparse
import json

INTRO = """
Apply controlled degradations to an audio file

Available degradations:
    noise,color='violet',snr=20
        Add noise to produce desired SNR
"""


def main():
    parser = argparse.ArgumentParser(
        prog="audio-degradation-toolbox",
        description=INTRO,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-d",
        "--degradation",
        action="append",
        nargs="?",
        help="Named degradations with their parameters in CSV",
    )
    parser.add_argument("input_path", help="Path to input file")
    parser.add_argument("output_path", help="Path to output WAV file")
    args = parser.parse_args()

    faudio = FileAudio(args.input_path)

    if args.degradation:
        for degradation in args.degradation:
            faudio.apply_degradation(degradation)

    faudio.export(args.output_path)
