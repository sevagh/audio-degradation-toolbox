#!/usr/bin/env python3

import unittest
from audio_degradation_toolbox.core import Degradation
import numpy
import math


# https://gist.github.com/sebpiq/4128537
def goertzel(samples, sample_rate, *freqs):
    window_size = len(samples)
    f_step = sample_rate / float(window_size)
    f_step_normalized = 1.0 / window_size

    bins = set()
    for f_range in freqs:
        f_start, f_end = f_range
        k_start = int(math.floor(f_start / f_step))
        k_end = int(math.ceil(f_end / f_step))

        if k_end > window_size - 1:
            raise ValueError("frequency out of range %s" % k_end)
        bins = bins.union(range(k_start, k_end))

    n_range = range(0, window_size)
    freqs = []
    results = []
    for k in bins:

        f = k * f_step_normalized
        w_real = 2.0 * math.cos(2.0 * math.pi * f)
        w_imag = math.sin(2.0 * math.pi * f)

        d1, d2 = 0.0, 0.0
        for n in n_range:
            y = samples[n] + w_real * d1 - d2
            d2, d1 = d1, y

        results.append(
            (0.5 * w_real * d1 - d2, w_imag * d1, d2 ** 2 + d1 ** 2 - w_real * d1 * d2)
        )
        freqs.append(f * sample_rate)
    return freqs, results


class TestAllDegradations(unittest.TestCase):
    def setUp(self):
        self.d = Degradation("./samples/Viola.arco.ff.sulC.E3.stereo.aiff")

    def test_basic(self):
        self.assertEqual(self.d.file_audio.sample_rate, 44100)
        self.assertEqual(len(self.d.file_audio.sound), 3664)

    def test_noise(self):
        prev_mean = numpy.mean(
            numpy.frombuffer(
                self.d.file_audio.samples, dtype=self.d.file_audio.sound.array_type
            )
        )

        noises = [
            {"name": "noise", "color": "pink"},
            {"name": "noise", "color": "white", "snr": 30},
            {"name": "noise", "color": "brown", "snr": 10},
            {"name": "noise", "color": "blue", "snr": 20},
            {"name": "noise", "color": "violet", "snr": 15},
        ]

        for noise in noises:
            self.d.apply_degradation(noise)
            new_mean = numpy.mean(
                numpy.frombuffer(
                    self.d.file_audio.samples, dtype=self.d.file_audio.sound.array_type
                )
            )
            # ensure the signal has a different mean after noise
            self.assertNotEqual(new_mean, prev_mean)
            prev_mean = new_mean

        # noise won't affect the length
        self.assertEqual(len(self.d.file_audio.sound), 3664)

    def test_mp3(self):
        mp3s = [
            {"name": "mp3"},
            {"name": "mp3", "bitrate": 128},
            {"name": "mp3", "bitrate": 64},
        ]

        for mp3 in mp3s:
            self.d.apply_degradation(mp3)

        self.assertTrue(len(self.d.file_audio.sound) > 3664)

    def test_gain(self):
        prev_max = numpy.max(
            numpy.frombuffer(
                self.d.file_audio.samples, dtype=self.d.file_audio.sound.array_type
            )
        )

        gains = [
            {"name": "gain"},
            {"name": "gain", "volume": -10},
            {"name": "gain", "volume": 10},
        ]

        for gain in gains:
            self.d.apply_degradation(gain)
            new_max = numpy.max(
                numpy.frombuffer(
                    self.d.file_audio.samples, dtype=self.d.file_audio.sound.array_type
                )
            )
            if gain.get("volume", 10) < 0:
                self.assertTrue(new_max < prev_max)
            else:
                self.assertTrue(new_max >= prev_max)
            prev_max = new_max

    def test_normalize(self):
        normalize = {"name": "normalize"}
        self.d.apply_degradation(normalize)

    def test_low_pass(self):
        # our input is E3 aka 160ish hz
        _, old = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )
        old_pwr = 0
        for o in old:
            old_pwr += o[2]

        low_pass = {"name": "low_pass", "cutoff": 100}
        self.d.apply_degradation(low_pass)
        _, new = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )

        new_pwr = 0
        for n in new:
            new_pwr += n[2]

        self.assertTrue(new_pwr < old_pwr)

    def test_high_pass(self):
        # our input is E3 aka 160ish hz
        _, old = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )
        old_pwr = 0
        for o in old:
            old_pwr += o[2]

        high_pass = {"name": "high_pass", "cutoff": 200}
        self.d.apply_degradation(high_pass)
        _, new = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )

        new_pwr = 0
        for n in new:
            new_pwr += n[2]

        self.assertTrue(new_pwr < old_pwr)

    def test_trim_millis(self):
        trim_left = {"name": "trim_millis"}
        trim_right = {"name": "trim_millis", "offset": -1, "amount": 500}
        self.d.apply_degradation(trim_left)
        self.d.apply_degradation(trim_right)

        self.assertEqual(len(self.d.file_audio.sound), 3664 - 100 - 500)


if __name__ == "__main__":
    unittest.main()
