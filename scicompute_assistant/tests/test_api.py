"""End-to-end tests against the FastAPI surface, using the stub LLM."""

from __future__ import annotations



def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "SciCompute-Assistant"
    assert "mode" in body


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_chat_with_stub(client):
    r = client.post(
        "/ai/chat",
        json={
            "messages": [{"role": "user", "content": "什么是 numpy 广播？"}],
            "provider": "server",
            "temperature": 0.1,
            "max_tokens": 256,
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["reply"]["role"] == "assistant"
    assert "stub-reply" in data["reply"]["content"]
    assert data["usage"]["provider"] == "server"


def test_audit_vectorize_stub_returns_valid_json(client):
    student_code = (
        "def sum_squares(arr):\n"
        "    total = 0\n"
        "    for x in arr:\n"
        "        total += x * x\n"
        "    return total\n"
    )
    r = client.post(
        "/ai/audit/vectorize",
        json={
            "code": student_code,
            "provider": "server",
            "course_week": 3,
            "target": "vectorize",
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["summary"]
    assert isinstance(data["suggestions"], list) and data["suggestions"]
    assert data["suggestions"][0]["category"] == "vectorization"
    assert "np.sum" in (data["refactored_code"] or "")


def test_compute_run_basic(client):
    r = client.post(
        "/compute/run",
        json={
            "code": "import numpy as np\nresult = {'mean': float(np.mean([1, 2, 3, 4]))}",
            "timeout_sec": 2.0,
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["ok"] is True, f"{data}"
    assert data["result"]["mean"] == 2.5


def test_compute_blocks_dangerous_imports(client):
    r = client.post(
        "/compute/run",
        json={
            "code": "import os\nresult = {'cwd': os.getcwd()}",
            "timeout_sec": 2.0,
        },
    )
    data = r.json()
    assert data["ok"] is False
    assert data["error"] in {"ImportError", "syntax"}


def test_tda_pipeline_with_circle(client):
    """A noisy 2-D circle should yield at least one H1 (or fallback H0) feature."""
    import math
    import random

    random.seed(0)
    cloud = []
    for i in range(60):
        theta = 2 * math.pi * i / 60
        r = 1.0 + 0.02 * random.random()
        cloud.append([r * math.cos(theta), r * math.sin(theta)])

    r = client.post(
        "/tda/pipeline",
        json={
            "data": cloud,
            "pipeline": "vietoris_rips",
            "max_dimension": 1,
            "max_edge_length": 2.0,
            "n_bins": 50,
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    diagram = data["diagram"]
    assert isinstance(diagram["points"], list) and diagram["points"]
    assert diagram["axis_limits"][1] >= 0
    # If giotto-tda is installed we expect at least one H1 feature, otherwise
    # the numpy fallback emits H0 only – just assert dims are valid.
    dims = {p["dimension"] for p in diagram["points"]}
    assert dims.issubset({0, 1, 2})


def test_knowledge_search_returns_courseware(tmp_path, monkeypatch):
    """Use an isolated courseware root so the test never writes into the repo."""
    monkeypatch.setenv("SCICOMP_COURSEWARE_ROOT", str(tmp_path))
    (tmp_path / "week03_numpy_test.md").write_text(
        "tags: week:3, numpy\n# NumPy 广播\nNumPy 通过 broadcasting 规则避免显式循环。",
        encoding="utf-8",
    )
    from fastapi.testclient import TestClient

    from scicompute_assistant.server import dependencies
    from scicompute_assistant.server.main import create_app

    for fn in (
        dependencies.get_settings,
        dependencies.get_orchestrator,
        dependencies.get_compute_kernel,
        dependencies.get_tda_engine,
        dependencies.get_knowledge_service,
    ):
        fn.cache_clear()

    with TestClient(create_app()) as client:
        r = client.get(
            "/knowledge/search",
            params={"q": "广播", "tag": "week:3", "k": 3},
        )
    assert r.status_code == 200
    body = r.json()
    assert body, body
    assert body[0]["doc_id"].endswith("week03_numpy_test.md")
