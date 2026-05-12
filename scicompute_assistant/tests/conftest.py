"""Shared pytest fixtures."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _disable_outbound_llm(monkeypatch):
    monkeypatch.setenv("SCICOMP_DISABLE_OUTBOUND_LLM", "true")
    monkeypatch.setenv("SCICOMP_SERVER_API_KEY", "")
    yield


@pytest.fixture()
def app():
    # Reset singletons so the disable flag takes effect.
    from scicompute_assistant.server import dependencies

    for fn in (
        dependencies.get_settings,
        dependencies.get_orchestrator,
        dependencies.get_compute_kernel,
        dependencies.get_tda_engine,
        dependencies.get_knowledge_service,
    ):
        fn.cache_clear()
    from scicompute_assistant.server.main import create_app

    return create_app()


@pytest.fixture()
def client(app):
    from fastapi.testclient import TestClient

    return TestClient(app)
