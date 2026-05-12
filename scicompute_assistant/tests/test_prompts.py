"""Sanity tests for the prompt library + audit parser."""

from __future__ import annotations

from scicompute_assistant.common.ai.orchestrator import AIOrchestrator
from scicompute_assistant.common.ai.prompts import (
    VECTORIZE_SYSTEM_PROMPT,
    PromptLibrary,
)
from scicompute_assistant.common.protocols.api_models import LLMUsage


def test_vectorize_prompt_carries_line_numbers():
    code = "a = 0\nfor x in arr:\n    a += x"
    msgs = PromptLibrary.vectorize_audit(
        code=code, course_week=3, target="vectorize", course_context="ctx"
    )
    assert msgs[0].role == "system"
    assert msgs[0].content == VECTORIZE_SYSTEM_PROMPT
    # All three lines must appear with line numbers.
    user = msgs[1].content
    assert "   1 |" in user and "   2 |" in user and "   3 |" in user
    assert "ctx" in user


def test_audit_parser_handles_clean_json():
    raw = (
        '{"summary":"ok","suggestions":'
        '[{"category":"vectorization","severity":"info","line_range":[1,2],'
        '"rationale":"r","rewritten_snippet":"x"}],'
        '"refactored_code":"y"}'
    )
    out = AIOrchestrator._parse_audit_response(raw, usage=LLMUsage())
    assert out.summary == "ok"
    assert out.refactored_code == "y"
    assert out.suggestions[0].category == "vectorization"


def test_audit_parser_strips_code_fences():
    raw = '```json\n{"summary":"a","suggestions":[],"refactored_code":null}\n```'
    out = AIOrchestrator._parse_audit_response(raw, usage=LLMUsage())
    assert out.summary == "a"
    assert out.suggestions == []


def test_audit_parser_falls_back_on_garbage():
    raw = "sorry, here is a thought\n{not valid json"
    out = AIOrchestrator._parse_audit_response(raw, usage=LLMUsage())
    assert "无法解析" in out.summary
