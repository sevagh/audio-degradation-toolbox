Python 3 implementation of the MATLAB [Audio Degradation Toolbox](https://code.soundsoftware.ac.uk/projects/audio-degradation-toolbox). The license is GPL due to the original code being GPL. The aim is full feature parity with:

* Original MATLAB toolbox (with ISMIR2013 additions)
* A similar tool, [audio_degrader](https://github.com/EliosMolina/audio_degrader)

This tool can read non-WAV files as input, but only outputs single-channel WAV files - this is because I find that WAV is the most universal format with friendly-licensed libraries in any language.

### Available degradations

```
$ audio-degradation-toolbox -h
usage: audio-degradation-toolbox [-h] [-d DEGRADATIONS_FILE] [-p] [-t]
                                 input_path output_path

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
    { "name": "delay", "n_samples": INT }
    { "name": "clipping", ["n_samples": 0, "percent_samples": 0.0] }
    { "name": "wow_flutter", ["intensity": 1.5, "frequency": 0.5, "upsampling_factor": 5.0 ] }
    { "name": "aliasing", ["dest_frequency": 8000.0] }
    { "name": "harmonic_distortion", ["num_passes": 3] }

positional arguments:
  input_path            Path to input file
  output_path           Path to output WAV file

optional arguments:
  -h, --help            show this help message and exit
  -d DEGRADATIONS_FILE, --degradations-file DEGRADATIONS_FILE
                        JSON file of degradations to apply
  -p, --play            Play file audio at each degradation step
  -t, --trim            Trim trailing and leading silences
```

### Presets and samples

Some of the ISMIR2013 degradations are chains of basic degradations. Given the JSON format that my tool accepts, these are most easily represented as JSON files in the [presets](./presets) dir.

[Samples](./samples), mostly IR wav files, come from the original MATLAB repository. I've resampled them from 96000 to 48000 with ffmpeg, since pydub has questionable support for 96000.

### Install, develop, contribute

It should be as easy as `pip3 install .` after cloning this repository. Afterwards, run `audio-degradation-toolbox`. You may need to install `sox` from your OS package manager for some effects.

To develop, `pip3 install -e .`. The code is formatted with [black](https://github.com/ambv/black), so run that before contributing anything.

To use the `--play` flag (i.e. play the audio clip between each degradation), you must have `mpv` installed and in `$PATH`:

```
sevagh:audio-degradation-toolbox $ audio-degradation-toolbox \
        Viola.arco.ff.sulC.E3.stereo.aiff \
        Viola-E3-degraded.wav \
        --degradations-file ./degradations.json \
        --play
Playing audio before degradations
A: 00:00:03 / 00:00:03 (93%)
Applied degradation noise with params color: white, snr: 20
Playing audio after degradation
A: 00:00:03 / 00:00:03 (93%)
```

### Usage

Write the desired degradations in a JSON file, e.g.:

```
$ cat degradations.json
[
  {
    "name": "trim_millis",
    "amount": 500
  },
  {
    "name": "noise",
    "color": "violet",
    "snr": 10
  },
  {
    "name": "mix",
    "path": "./restaurant08.wav",
    "snr": 15
  }
]
```

Afterwards, apply the degradations with:

```
$ audio-degradation-toolbox -d degradations.json in.wav out_degraded.wav
```

### Unimplemented

MfccMeanAdaption and AdaptiveEqualizer (both from the MATLAB original).
