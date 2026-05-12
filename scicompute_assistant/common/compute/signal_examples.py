"""Robust SciPy signal-processing examples used by the compute kernel."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy import signal


FilterKind = Literal["lowpass", "highpass", "bandpass", "bandstop"]


@dataclass(frozen=True)
class SignalSeries:
    """A one-dimensional sampled signal plus metadata."""

    samples: list[float]
    sample_rate_hz: float
    time_seconds: list[float]
    metadata: dict[str, float | int | str] = field(default_factory=dict)


@dataclass(frozen=True)
class SpectrumSeries:
    """Frequency-domain representation of a signal."""

    frequencies_hz: list[float]
    amplitudes: list[float]
    metadata: dict[str, float | int | str] = field(default_factory=dict)


@dataclass(frozen=True)
class SpectrogramSeries:
    """Time-frequency power representation."""

    frequencies_hz: list[float]
    time_seconds: list[float]
    power: list[list[float]]
    metadata: dict[str, float | int | str] = field(default_factory=dict)


def demo_signal(
    *,
    sample_rate_hz: float = 200.0,
    duration_seconds: float = 1.0,
    low_frequency_hz: float = 5.0,
    high_frequency_hz: float = 40.0,
) -> SignalSeries:
    """Create a deterministic two-tone signal for classroom examples."""

    sample_rate = _safe_sample_rate(sample_rate_hz)
    duration = max(float(duration_seconds), 0.0)
    n_samples = max(int(round(sample_rate * duration)), 0)
    if n_samples == 0:
        return _series_from_array(np.empty(0, dtype=np.float64), sample_rate, {"kind": "demo"})
    t = np.arange(n_samples, dtype=np.float64) / sample_rate
    samples = np.sin(2.0 * np.pi * low_frequency_hz * t)
    samples += 0.35 * np.sin(2.0 * np.pi * high_frequency_hz * t)
    return _series_from_array(samples, sample_rate, {"kind": "demo"})


def butterworth_filter(
    samples: ArrayLike,
    *,
    sample_rate_hz: float,
    cutoff_hz: float | tuple[float, float],
    order: int = 4,
    kind: FilterKind = "lowpass",
) -> SignalSeries:
    """Apply a Butterworth filter with safeguards for short or dirty signals."""

    x = sanitize_signal(samples)
    sample_rate = _safe_sample_rate(sample_rate_hz)
    if x.size == 0:
        return _series_from_array(x, sample_rate, {"kind": kind, "order": max(order, 1)})

    clipped_cutoff = _clip_cutoff(cutoff_hz, sample_rate, kind)
    safe_order = int(np.clip(order, 1, 12))
    sos = signal.butter(
        safe_order,
        clipped_cutoff,
        btype=kind,
        fs=sample_rate,
        output="sos",
    )
    # sosfiltfilt needs padding; fall back to causal filtering for tiny examples.
    padlen = 3 * (2 * sos.shape[0] + 1)
    filtered = signal.sosfiltfilt(sos, x) if x.size > padlen else signal.sosfilt(sos, x)
    return _series_from_array(
        sanitize_signal(filtered),
        sample_rate,
        {"kind": kind, "order": safe_order},
    )


def fft_spectrum(samples: ArrayLike, *, sample_rate_hz: float) -> SpectrumSeries:
    """Return a Hann-windowed one-sided FFT amplitude spectrum."""

    x = sanitize_signal(samples)
    sample_rate = _safe_sample_rate(sample_rate_hz)
    if x.size == 0:
        return SpectrumSeries(frequencies_hz=[], amplitudes=[], metadata={"kind": "fft"})
    centered = x - float(np.mean(x))
    window = signal.windows.hann(x.size, sym=False) if x.size > 1 else np.ones_like(x)
    scale = max(float(np.sum(window)), np.finfo(np.float64).eps)
    spectrum = np.fft.rfft(centered * window)
    frequencies = np.fft.rfftfreq(x.size, d=1.0 / sample_rate)
    amplitudes = 2.0 * np.abs(spectrum) / scale
    return SpectrumSeries(
        frequencies_hz=_finite_list(frequencies),
        amplitudes=_finite_list(amplitudes),
        metadata={"kind": "fft", "n_samples": int(x.size)},
    )


def welch_power_spectrum(
    samples: ArrayLike,
    *,
    sample_rate_hz: float,
    nperseg: int = 256,
) -> SpectrumSeries:
    """Estimate power spectral density with :func:`scipy.signal.welch`."""

    x = sanitize_signal(samples)
    sample_rate = _safe_sample_rate(sample_rate_hz)
    if x.size == 0:
        return SpectrumSeries(frequencies_hz=[], amplitudes=[], metadata={"kind": "welch"})
    segment = int(np.clip(nperseg, 1, max(int(x.size), 1)))
    frequencies, power = signal.welch(x, fs=sample_rate, nperseg=segment)
    return SpectrumSeries(
        frequencies_hz=_finite_list(frequencies),
        amplitudes=_finite_list(power),
        metadata={"kind": "welch", "nperseg": segment},
    )


def spectrogram_example(
    samples: ArrayLike,
    *,
    sample_rate_hz: float,
    nperseg: int = 128,
) -> SpectrogramSeries:
    """Compute a compact spectrogram suitable for plotting as a heatmap."""

    x = sanitize_signal(samples)
    sample_rate = _safe_sample_rate(sample_rate_hz)
    if x.size == 0:
        return SpectrogramSeries(
            frequencies_hz=[],
            time_seconds=[],
            power=[],
            metadata={"kind": "spectrogram"},
        )
    segment = int(np.clip(nperseg, 1, max(int(x.size), 1)))
    frequencies, times, power = signal.spectrogram(x, fs=sample_rate, nperseg=segment)
    clean_power = sanitize_signal(power.ravel()).reshape(power.shape)
    return SpectrogramSeries(
        frequencies_hz=_finite_list(frequencies),
        time_seconds=_finite_list(times),
        power=[_finite_list(row) for row in clean_power],
        metadata={"kind": "spectrogram", "nperseg": segment},
    )


def resample_signal(
    samples: ArrayLike,
    *,
    sample_rate_hz: float,
    target_sample_rate_hz: float,
) -> SignalSeries:
    """Resample a signal with Fourier resampling."""

    x = sanitize_signal(samples)
    sample_rate = _safe_sample_rate(sample_rate_hz)
    target_rate = _safe_sample_rate(target_sample_rate_hz)
    if x.size == 0:
        return _series_from_array(x, target_rate, {"kind": "resample"})
    target_size = max(int(round(x.size * target_rate / sample_rate)), 1)
    resampled = signal.resample(x, target_size)
    return _series_from_array(
        sanitize_signal(resampled),
        target_rate,
        {"kind": "resample", "source_sample_rate_hz": sample_rate},
    )


def cross_correlation(
    left: ArrayLike,
    right: ArrayLike,
    *,
    sample_rate_hz: float,
) -> SignalSeries:
    """Compute normalized full cross-correlation between two signals."""

    x = sanitize_signal(left)
    y = sanitize_signal(right)
    sample_rate = _safe_sample_rate(sample_rate_hz)
    if x.size == 0 or y.size == 0:
        return SignalSeries(samples=[], sample_rate_hz=sample_rate, time_seconds=[], metadata={"kind": "xcorr"})
    x = x - float(np.mean(x))
    y = y - float(np.mean(y))
    corr = signal.correlate(x, y, mode="full", method="auto")
    denom = max(float(np.linalg.norm(x) * np.linalg.norm(y)), np.finfo(np.float64).eps)
    corr = sanitize_signal(corr / denom)
    lags = signal.correlation_lags(x.size, y.size, mode="full") / sample_rate
    return SignalSeries(
        samples=_finite_list(corr),
        sample_rate_hz=sample_rate,
        time_seconds=_finite_list(lags),
        metadata={"kind": "xcorr"},
    )


def sanitize_signal(samples: ArrayLike) -> NDArray[np.float64]:
    """Convert arbitrary input into a finite float64 ndarray."""

    try:
        arr = np.asarray(samples, dtype=np.float64)
    except (TypeError, ValueError):
        return np.empty(0, dtype=np.float64)
    if arr.size == 0:
        return np.empty(0, dtype=np.float64)
    arr = np.ravel(arr).astype(np.float64, copy=False)
    finite_mask = np.isfinite(arr)
    if np.all(finite_mask):
        return arr
    finite_values = arr[finite_mask]
    fill = float(np.median(finite_values)) if finite_values.size else 0.0
    return np.where(finite_mask, arr, fill).astype(np.float64, copy=False)


def _safe_sample_rate(sample_rate_hz: float) -> float:
    value = float(sample_rate_hz) if np.isfinite(sample_rate_hz) else 1.0
    return max(value, np.finfo(np.float64).eps)


def _clip_cutoff(
    cutoff_hz: float | tuple[float, float],
    sample_rate_hz: float,
    kind: FilterKind,
) -> float | tuple[float, float]:
    nyquist = sample_rate_hz / 2.0
    eps = max(nyquist * 1e-6, np.finfo(np.float64).eps)
    if kind in {"bandpass", "bandstop"}:
        if not isinstance(cutoff_hz, tuple) or len(cutoff_hz) != 2:
            raw_low, raw_high = nyquist * 0.1, nyquist * 0.4
        else:
            raw_low, raw_high = cutoff_hz
        low = float(raw_low) if np.isfinite(raw_low) else eps
        high = float(raw_high) if np.isfinite(raw_high) else nyquist - eps
        low = float(np.clip(low, eps, nyquist - 2 * eps))
        high = float(np.clip(high, low + eps, nyquist - eps))
        return (low, high)

    raw = cutoff_hz[0] if isinstance(cutoff_hz, tuple) else cutoff_hz
    value = float(raw) if np.isfinite(raw) else nyquist * 0.25
    return float(np.clip(value, eps, nyquist - eps))


def _series_from_array(
    samples: NDArray[np.float64],
    sample_rate_hz: float,
    metadata: dict[str, float | int | str],
) -> SignalSeries:
    clean = sanitize_signal(samples)
    time = np.arange(clean.size, dtype=np.float64) / _safe_sample_rate(sample_rate_hz)
    return SignalSeries(
        samples=_finite_list(clean),
        sample_rate_hz=_safe_sample_rate(sample_rate_hz),
        time_seconds=_finite_list(time),
        metadata=metadata,
    )


def _finite_list(values: ArrayLike) -> list[float]:
    arr = sanitize_signal(values)
    return [float(value) for value in arr.tolist()]
