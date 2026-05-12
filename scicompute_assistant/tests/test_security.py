"""Tests for the local encrypted key store."""

from __future__ import annotations

import pytest

from scicompute_assistant.common.security import (
    EncryptedFileStore,
    NullStore,
    build_default_store,
)


def test_encrypted_file_store_roundtrip(tmp_path):
    path = tmp_path / "keys.enc.json"
    store = EncryptedFileStore(path=path, passphrase="hunter2-very-secret")
    store.set_secret("llm:deepseek:default", "sk-test-abc")
    assert store.get_secret("llm:deepseek:default") == "sk-test-abc"
    assert "llm:deepseek:default" in set(store.list_aliases())

    # Re-open with the same passphrase – should decrypt successfully.
    again = EncryptedFileStore(path=path, passphrase="hunter2-very-secret")
    assert again.get_secret("llm:deepseek:default") == "sk-test-abc"

    again.delete_secret("llm:deepseek:default")
    assert again.get_secret("llm:deepseek:default") is None


def test_encrypted_file_store_rejects_wrong_passphrase(tmp_path):
    path = tmp_path / "keys.enc.json"
    EncryptedFileStore(path=path, passphrase="correct").set_secret("k", "v")
    with pytest.raises(PermissionError):
        EncryptedFileStore(path=path, passphrase="wrong")


def test_null_store_is_read_only():
    s = NullStore()
    assert s.get_secret("anything") is None
    with pytest.raises(RuntimeError):
        s.set_secret("k", "v")


def test_build_default_store_server_mode():
    s = build_default_store(mode="server")
    assert isinstance(s, NullStore)


def test_build_default_store_desktop_fallback(tmp_path):
    s = build_default_store(
        mode="desktop",
        fallback_path=tmp_path / "k.json",
        fallback_passphrase="pp",
    )
    assert isinstance(s, EncryptedFileStore)
