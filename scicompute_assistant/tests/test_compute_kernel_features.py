"""Focused tests for the NumPy/SciPy/giotto-tda compute-kernel helpers."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import numpy as np

from scicompute_assistant.common.compute import ComputeKernel, audit_vectorized_code


def _load_function(source: str, name: str) -> Callable[[Any], Any]:
    namespace: dict[str, Any] = {}
    exec(source, namespace)  # noqa: S102 - test-only execution of generated code
    fn = namespace[name]
    assert callable(fn)
    return fn


def test_persistent_homology_returns_plotly_traces_and_filters_nonfinite_points() -> None:
    kernel = ComputeKernel()
    response = kernel.persistent_homology(
        [
            [0.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [math.nan, 1.0],
            [math.inf, 2.0],
        ],
        max_dimension=1,
        max_edge_length=2.0,
        n_bins=20,
    )

    assert response.diagram.points
    assert response.diagram.plotly_traces
    assert response.diagram.plotly_traces[-1]["mode"] == "lines"
    assert all(math.isfinite(point.birth) and math.isfinite(point.death) for point in response.diagram.points)
    assert response.diagram.point_cloud_preview is not None
    assert len(response.diagram.point_cloud_preview) == 3
    assert any("Dropped 2 point" in warning for warning in response.warnings)


def test_persistent_homology_empty_cloud_is_empty_plotly_payload() -> None:
    kernel = ComputeKernel()
    response = kernel.persistent_homology([], max_dimension=1, max_edge_length=1.5)

    assert response.diagram.points == []
    assert response.diagram.plotly_traces[-1]["x"] == [0.0, 1.5]
    assert response.diagram.point_cloud_preview is None
    assert response.warnings


def test_vectorization_audit_rewrites_sum_squares_and_generated_code_runs() -> None:
    source = (
        "def sum_squares(arr):\n"
        "    total = 0\n"
        "    for x in arr:\n"
        "        total += x * x\n"
        "    return total\n"
    )

    result = audit_vectorized_code(source)

    assert result.changed is True
    assert result.refactored_code is not None
    assert "np.sum" in result.refactored_code
    assert "for x in arr" not in result.refactored_code
    fn = _load_function(result.refactored_code, "sum_squares")
    assert fn([1.0, 2.0, 3.0]) == 14.0
    assert fn([1.0, math.nan, math.inf]) == 1.0


def test_vectorization_audit_rewrites_indexed_assignment() -> None:
    source = (
        "import numpy as np\n\n"
        "def add_arrays(a, b):\n"
        "    out = np.zeros_like(a)\n"
        "    for i in range(len(a)):\n"
        "        out[i] = a[i] + 2 * b[i]\n"
        "    return out\n"
    )

    result = audit_vectorized_code(source)

    assert result.changed is True
    assert result.refactored_code is not None
    assert "return a + 2 * b" in result.refactored_code
    fn = _load_function(result.refactored_code, "add_arrays")
    np.testing.assert_allclose(fn([1, 2, 3], [4, 5, 6]), np.array([9.0, 12.0, 15.0]))


def test_signal_examples_handle_empty_and_nonfinite_values() -> None:
    kernel = ComputeKernel()
    samples = np.array([0.0, 1.0, np.nan, np.inf, -1.0, 0.5, -0.5, 0.0])

    filtered = kernel.lowpass_filter(samples, sample_rate_hz=100.0, cutoff_hz=10.0)
    spectrum = kernel.fft_spectrum(samples, sample_rate_hz=100.0)
    spectrogram = kernel.spectrogram(samples, sample_rate_hz=100.0, nperseg=4)
    resampled = kernel.resample(samples, sample_rate_hz=100.0, target_sample_rate_hz=50.0)
    empty_bandpass = kernel.bandpass_filter([], sample_rate_hz=100.0, low_hz=5.0, high_hz=20.0)

    assert len(filtered.samples) == samples.size
    assert all(math.isfinite(value) for value in filtered.samples)
    assert spectrum.frequencies_hz and all(math.isfinite(value) for value in spectrum.amplitudes)
    assert spectrogram.power and all(math.isfinite(value) for row in spectrogram.power for value in row)
    assert len(resampled.samples) == 4
    assert empty_bandpass.samples == []
