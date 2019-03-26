Python 3 implementation of the MATLAB [Audio Degradation Toolbox](https://code.soundsoftware.ac.uk/projects/audio-degradation-toolbox). The license is GPL due to the original code being GPL. The aim is full feature parity with:

* Original MATLAB toolbox (with ISMIR2013 additions)
* A similar tool, [audio_degrader](https://github.com/EliosMolina/audio_degrader)

I rely on a number of Python packages including pydub, scipy, numpy, and acoustics.

This tool can read non-WAV files as input, but only outputs single-channel WAV files - this is because I find that WAV is the most universal format with friendly-licensed libraries in any language.

### Install, develop, contribute

It should be as easy as `pip3 install .` after cloning this repository. Afterwards, run `audio-degradation-toolbox`.

To develop, `pip3 install -e .`. The code is formatted with [black](https://github.com/ambv/black), so run that before contributing anything.

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

Full usage text, with a listing of all available degradations:

```
usage: audio-degradation-toolbox [-h] [-d DEGRADATIONS_FILE] [-p]
                                 input_path output_path

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

positional arguments:
  input_path            Path to input file
  output_path           Path to output WAV file

optional arguments:
  -h, --help            show this help message and exit
  -d DEGRADATIONS_FILE, --degradations-file DEGRADATIONS_FILE
                        JSON file of degradations to apply
  -p, --play            Play file audio at each degradation step
```
