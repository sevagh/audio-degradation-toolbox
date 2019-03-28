import unittest
from audio_degradation_toolbox.core import Degradation
import numpy
import scipy.signal as scipy_signal
import math
import copy
import numba


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

    power = 0
    for r in results:
        power += r[2]
    return power


class TestAllDegradations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # don't reload the file so many times
        cls.orig_d = Degradation("./samples/Viola.arco.ff.sulC.E3.stereo.aiff")

    def setUp(self):
        self.d = copy.deepcopy(self.orig_d)

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
        old_pwr = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )

        low_pass = {"name": "low_pass", "cutoff": 100}
        self.d.apply_degradation(low_pass)
        new_pwr = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )

        self.assertTrue(new_pwr < old_pwr)

    def test_high_pass(self):
        # our input is E3 aka 160ish hz
        old_pwr = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )

        high_pass = {"name": "high_pass", "cutoff": 200}
        self.d.apply_degradation(high_pass)
        new_pwr = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )

        self.assertTrue(new_pwr < old_pwr)

    def test_trim_millis(self):
        trim_left = {"name": "trim_millis"}
        trim_right = {"name": "trim_millis", "offset": -1, "amount": 500}
        self.d.apply_degradation(trim_left)
        self.d.apply_degradation(trim_right)

        self.assertEqual(len(self.d.file_audio.sound), 3664 - 100 - 500)

    def test_mix(self):
        # our input is E3 aka 160ish hz
        old_pwr = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )

        mix = {"name": "mix", "path": "./samples/Viola.arco.ff.sulC.E3.stereo.aiff"}
        self.d.apply_degradation(mix)
        new_pwr = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )

        self.assertTrue(new_pwr > old_pwr)

    def test_speedup(self):
        speedup = {"name": "speedup", "speed": 1.05}
        old_fs = self.d.file_audio.sample_rate
        self.d.apply_degradation(speedup)

        self.assertEqual(old_fs / 1.05, self.d.file_audio.sample_rate)
        old_fs = self.d.file_audio.sample_rate

        speedup = {"name": "speedup", "speed": 0.95}
        self.d.apply_degradation(speedup)

        self.assertEqual(math.floor(old_fs / 0.95), self.d.file_audio.sample_rate)

    def test_resample(self):
        resample = {"name": "resample", "rate": 96000}
        self.assertNotEqual(self.d.file_audio.sample_rate, 96000)
        self.d.apply_degradation(resample)
        self.assertEqual(self.d.file_audio.sample_rate, 96000)

    def test_pitch_shift(self):
        # our input is E3 aka 160ish hz
        old_pwr = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )

        pitch_shift = {"name": "pitch_shift", "octaves": -1.0}

        self.d.apply_degradation(pitch_shift)
        new_pwr = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )

        self.assertTrue(new_pwr < old_pwr)

    def test_dynamic_range_compression(self):
        old_pwr = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )

        drcs = [
            {"name": "dynamic_range_compression"},
            {"name": "dynamic_range_compression", "threshold": -15.0, "ratio": 3.0},
            {"name": "dynamic_range_compression", "threshold": -15.0, "attack": 4.0},
            {"name": "dynamic_range_compression", "release": 42.0},
        ]

        for drc in drcs:
            self.d.apply_degradation(drc)
            new_pwr = goertzel(
                self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
            )

            self.assertTrue(new_pwr < old_pwr)

    def test_ir(self):
        old_pwr = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )

        ir = {"name": "impulse_response", "path": "./samples/IR_GreatHall.wav"}
        self.d.apply_degradation(ir)
        new_pwr = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )

        self.assertTrue(new_pwr > old_pwr)

    def test_eq(self):
        old_pwr = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )

        eq = {"name": "equalizer", "frequency": 163}
        self.d.apply_degradation(eq)
        new_pwr = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )

        self.assertTrue(new_pwr > old_pwr)

    def test_time_stretch(self):
        ts = {"name": "time_stretch", "factor": 2.0}
        self.d.apply_degradation(ts)
        self.assertTrue(3664 / 2.1 <= len(self.d.file_audio.sound) <= 3664 / 2.0)

    def test_delay(self):
        delay = {"name": "delay", "samples": 44100}
        self.d.apply_degradation(delay)
        self.assertEqual(len(self.d.file_audio.sound), 3664 + 1000)

    def test_clipping(self):
        _, old_pwr = scipy_signal.welch(
            self.d.file_audio.samples, self.d.file_audio.sample_rate
        )
        old_pwr = numpy.sum(old_pwr)

        clip = {"name": "clipping", "percent_samples": 50}
        self.d.apply_degradation(clip)

        _, new_pwr = scipy_signal.welch(
            self.d.file_audio.samples, self.d.file_audio.sample_rate
        )
        new_pwr = numpy.sum(new_pwr)

        self.assertTrue(new_pwr > old_pwr)

    def test_wow_flutter(self):
        old_pwr = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )

        wfs = [
            {"name": "wow_flutter"},
            {
                "name": "wow_flutter",
                "intensity": 3.0,
                "frequency": 0.5,
                "upsampling_factor": 1.0,
            },
        ]

        for wf in wfs:
            self.d.apply_degradation(wf)
            new_pwr = goertzel(
                self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
            )
            self.assertTrue(new_pwr < old_pwr)

    def test_aliasing(self):
        old_pwr = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )

        aliasing = {"name": "aliasing", "dest_frequency": 82.4}
        self.d.apply_degradation(aliasing)

        new_pwr = goertzel(
            self.d.file_audio.samples, self.d.file_audio.sample_rate, (162, 164)
        )
        self.assertTrue(new_pwr < old_pwr)

    def test_harmonic_distortion(self):
        _, old_pwr = scipy_signal.welch(
            self.d.file_audio.samples, self.d.file_audio.sample_rate
        )
        old_pwr = numpy.sum(old_pwr)

        hd = {"name": "harmonic_distortion", "num_passes": 5}
        self.d.apply_degradation(hd)

        _, new_pwr = scipy_signal.welch(
            self.d.file_audio.samples, self.d.file_audio.sample_rate
        )
        new_pwr = numpy.sum(new_pwr)

        self.assertTrue(new_pwr > old_pwr)


if __name__ == "__main__":
    unittest.main()
