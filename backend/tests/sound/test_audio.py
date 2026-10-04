import numpy as np
import pytest

from preflight.sound import audio, dsp


def test_pcm_round_trips_within_one_quantisation_step() -> None:
    samples = np.linspace(-0.9, 0.9, 1000, dtype=np.float32)

    decoded = audio.pcm16_to_float(audio.float_to_pcm16(samples))

    assert np.max(np.abs(decoded - samples)) < 2 / 32768


def test_resampling_keeps_pitch_and_scales_length() -> None:
    t = np.arange(24_000) / 24_000
    tone = np.sin(2 * np.pi * 440 * t).astype(np.float32)

    up = audio.resample(tone, 24_000, 48_000)

    assert len(up) == 48_000
    assert np.argmax(np.abs(np.fft.rfft(up))) == 440


def test_resampling_to_the_same_rate_is_a_no_op() -> None:
    samples = np.ones(10, dtype=np.float32)
    assert audio.resample(samples, 48_000, 48_000) is samples


def test_trim_silence_keeps_the_sound_and_a_short_margin() -> None:
    quiet = np.zeros(24_000, dtype=np.float32)
    burst = np.full(2_400, 0.5, dtype=np.float32)
    clip = np.concatenate([quiet, burst, quiet])

    trimmed = audio.trim_silence(clip)

    assert len(burst) < len(trimmed) < len(burst) + 2 * dsp.seconds(0.03) + 1


def test_trimming_pure_silence_returns_nothing() -> None:
    assert len(audio.trim_silence(np.zeros(1000, dtype=np.float32))) == 0


def test_deglitch_tail_drops_a_clipped_burst_after_the_word() -> None:
    rate = 24_000
    word = (0.4 * np.sin(2 * np.pi * 220 * np.arange(rate) / rate)).astype(np.float32)
    burst = np.full(int(0.03 * rate), 0.99, dtype=np.float32)
    cleaned = audio.deglitch_tail(np.concatenate([word, burst]), rate)

    assert len(cleaned) < len(word) + len(burst)
    assert float(np.max(np.abs(cleaned[-int(0.01 * rate) :]))) < 0.95


def test_deglitch_leaves_ordinary_speech_alone() -> None:
    rate = 24_000
    word = (0.4 * np.sin(2 * np.pi * 220 * np.arange(rate) / rate)).astype(np.float32)
    assert np.array_equal(audio.deglitch_tail(word, rate), word)


def test_fade_edges_starts_and_ends_at_zero() -> None:
    tone = np.ones(48_000, dtype=np.float32)
    faded = audio.fade_edges(tone, 48_000, in_s=0.01, out_s=0.05)
    assert faded[0] == 0.0 and faded[-1] == 0.0
    assert faded[24_000] == pytest.approx(1.0)


def test_rms_normalise_hits_the_target_without_clipping() -> None:
    t = np.arange(48_000) / 48_000
    tone = (0.05 * np.sin(2 * np.pi * 200 * t)).astype(np.float32)

    levelled = audio.rms_normalise(tone, -19.0)

    rms_db = 20 * np.log10(np.sqrt(np.mean(levelled**2)))
    assert rms_db == pytest.approx(-19.0, abs=0.1)
    assert np.max(np.abs(levelled)) < 0.9


def test_wav_files_round_trip_mono_pcm(tmp_path) -> None:
    pcm = audio.float_to_pcm16(np.linspace(-0.5, 0.5, 480, dtype=np.float32))

    audio.write_pcm_wav(tmp_path / "x.wav", pcm, 24_000)

    assert audio.read_wav_mono_pcm(tmp_path / "x.wav") == (pcm, 24_000)
    assert not list(tmp_path.glob("*.tmp"))
