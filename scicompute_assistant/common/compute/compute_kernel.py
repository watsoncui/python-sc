"""Compatibility module for the Opus-style ``compute_kernel.py`` interface."""

from __future__ import annotations

from .kernel import ComputeKernel
from .signal_examples import (
    SignalSeries,
    SpectrogramSeries,
    SpectrumSeries,
    bandpass_filter,
    butterworth_filter,
    cross_correlation,
    demo_signal,
    fft_spectrum,
    resample_signal,
    spectrogram_example,
    welch_power_spectrum,
)
from .vectorization import (
    VectorizationAuditResult,
    VectorizationSuggestion,
    audit_vectorized_code,
)

__all__ = [
    "ComputeKernel",
    "SignalSeries",
    "SpectrogramSeries",
    "SpectrumSeries",
    "VectorizationAuditResult",
    "VectorizationSuggestion",
    "audit_vectorized_code",
    "bandpass_filter",
    "butterworth_filter",
    "cross_correlation",
    "demo_signal",
    "fft_spectrum",
    "resample_signal",
    "spectrogram_example",
    "welch_power_spectrum",
]
