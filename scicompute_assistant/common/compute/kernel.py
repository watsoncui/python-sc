"""High-level compute facade used by FastAPI routers.

Wraps the lower-level :class:`Sandbox` and exposes:

* ``run_code`` – generic execution with stdout/stderr capture.
* ``run_with_dataset`` – passes a NumPy array into the sandbox namespace.

Heavy lifting (TDA, ODE solvers, etc.) lives in dedicated modules; this
facade is intentionally thin so the route layer stays trivial.
"""

from __future__ import annotations

from typing import Any

from numpy.typing import ArrayLike

from ..protocols.tda_payload import TDARequest, TDAResponse
from .signal_examples import (
    SignalSeries,
    SpectrogramSeries,
    SpectrumSeries,
    butterworth_filter,
    cross_correlation,
    demo_signal,
    fft_spectrum,
    resample_signal,
    spectrogram_example,
    welch_power_spectrum,
)
from .sandbox import Sandbox, SandboxResult
from .tda import TDAEngine
from .vectorization import VectorizationAuditResult, audit_vectorized_code


class ComputeKernel:
    def __init__(self, *, timeout_sec: float = 5.0, restricted: bool = True) -> None:
        self._timeout = timeout_sec
        self._restricted = restricted
        self._tda = TDAEngine()

    def run_code(
        self,
        code: str,
        *,
        inputs: dict[str, Any] | None = None,
        timeout_sec: float | None = None,
    ) -> SandboxResult:
        sandbox = Sandbox(
            timeout_sec=timeout_sec if timeout_sec is not None else self._timeout,
            allow_restricted=self._restricted,
        )
        return sandbox.run(code, inputs=inputs or {})

    def persistent_homology(
        self,
        data: list[list[float]],
        *,
        pipeline: str = "vietoris_rips",
        max_dimension: int = 2,
        max_edge_length: float = 1.0,
        n_bins: int = 100,
        downsample_preview: int = 500,
    ) -> TDAResponse:
        """Compute persistent homology and return Plotly-ready diagram data."""

        req = TDARequest(
            data=data,
            pipeline=pipeline,  # type: ignore[arg-type]
            max_dimension=max_dimension,
            max_edge_length=max_edge_length,
            n_bins=n_bins,
            downsample_preview=downsample_preview,
        )
        return self._tda.compute(req)

    def audit_vectorization(self, code: str) -> VectorizationAuditResult:
        """Audit and conservatively rewrite explicit loops into NumPy operations."""

        return audit_vectorized_code(code)

    def signal_demo(
        self,
        *,
        sample_rate_hz: float = 200.0,
        duration_seconds: float = 1.0,
    ) -> SignalSeries:
        """Generate a deterministic noisy signal for SciPy examples."""

        return demo_signal(sample_rate_hz=sample_rate_hz, duration_seconds=duration_seconds)

    def lowpass_filter(
        self,
        samples: ArrayLike,
        *,
        sample_rate_hz: float,
        cutoff_hz: float,
        order: int = 4,
    ) -> SignalSeries:
        """Example: remove high-frequency components with SciPy Butterworth filtering."""

        return butterworth_filter(
            samples,
            sample_rate_hz=sample_rate_hz,
            cutoff_hz=cutoff_hz,
            order=order,
            kind="lowpass",
        )

    def bandpass_filter(
        self,
        samples: ArrayLike,
        *,
        sample_rate_hz: float,
        low_hz: float,
        high_hz: float,
        order: int = 4,
    ) -> SignalSeries:
        """Example: keep a frequency band with SciPy Butterworth filtering."""

        return butterworth_filter(
            samples,
            sample_rate_hz=sample_rate_hz,
            cutoff_hz=(low_hz, high_hz),
            order=order,
            kind="bandpass",
        )

    def fft_spectrum(self, samples: ArrayLike, *, sample_rate_hz: float) -> SpectrumSeries:
        """Example: compute a one-sided FFT amplitude spectrum."""

        return fft_spectrum(samples, sample_rate_hz=sample_rate_hz)

    def welch_power_spectrum(
        self,
        samples: ArrayLike,
        *,
        sample_rate_hz: float,
        nperseg: int = 256,
    ) -> SpectrumSeries:
        """Example: estimate power spectral density with Welch averaging."""

        return welch_power_spectrum(samples, sample_rate_hz=sample_rate_hz, nperseg=nperseg)

    def spectrogram(
        self,
        samples: ArrayLike,
        *,
        sample_rate_hz: float,
        nperseg: int = 128,
    ) -> SpectrogramSeries:
        """Example: compute a time-frequency spectrogram."""

        return spectrogram_example(samples, sample_rate_hz=sample_rate_hz, nperseg=nperseg)

    def resample(
        self,
        samples: ArrayLike,
        *,
        sample_rate_hz: float,
        target_sample_rate_hz: float,
    ) -> SignalSeries:
        """Example: resample a signal to a new sampling rate."""

        return resample_signal(
            samples,
            sample_rate_hz=sample_rate_hz,
            target_sample_rate_hz=target_sample_rate_hz,
        )

    def cross_correlation(
        self,
        left: ArrayLike,
        right: ArrayLike,
        *,
        sample_rate_hz: float,
    ) -> SignalSeries:
        """Example: compute normalized full cross-correlation."""

        return cross_correlation(left, right, sample_rate_hz=sample_rate_hz)
