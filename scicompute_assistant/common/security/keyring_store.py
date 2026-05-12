"""Local key storage abstraction for the desktop build.

We support three concrete strategies:

1. :class:`TauriKeyringStore` – preferred. Delegates to the OS keychain
   (macOS Keychain, Windows Credential Manager, libsecret) **via** Tauri's
   ``tauri-plugin-stronghold`` / ``tauri-plugin-keyring`` IPC. The Python
   side never sees the raw key on disk.

2. :class:`EncryptedFileStore` – fallback for headless test runs and Linux
   distros where libsecret is missing. Uses ``Fernet`` (AES-128-CBC + HMAC)
   with a key derived from a user-chosen passphrase (PBKDF2-HMAC-SHA256,
   600k iterations – matches OWASP 2025 baseline).

3. :class:`NullStore` – the server build. ``get_secret`` always returns
   ``None`` so any accidental call to a "local" code path fails fast and
   loud instead of silently calling out with no key.

The dispatcher :func:`build_default_store` chooses based on the runtime
environment so the same ``LocalProvider`` works in both desktop and
test contexts without code changes.
"""

from __future__ import annotations

import abc
import base64
import json
import os
import secrets
from pathlib import Path
from typing import Callable, Iterable

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecurityStore(abc.ABC):
    """Strict contract for any concrete secret store."""

    @abc.abstractmethod
    def get_secret(self, name: str) -> str | None: ...

    @abc.abstractmethod
    def set_secret(self, name: str, value: str) -> None: ...

    @abc.abstractmethod
    def delete_secret(self, name: str) -> None: ...

    @abc.abstractmethod
    def list_aliases(self) -> Iterable[str]: ...


# --------------------------------------------------------------------------- #
# 1. Tauri keyring bridge
# --------------------------------------------------------------------------- #
class TauriKeyringStore(SecurityStore):
    """Bridges Python <-> Tauri IPC for OS-native secret storage.

    The expectation is that ``invoke_fn`` is the same JS-side ``invoke`` proxy
    exposed by Tauri's sidecar layer (or by pywebview in a fallback build).
    Implementations of ``invoke_fn`` should call into the Rust side, which
    in turn talks to:

        macOS    →  Keychain Services
        Windows  →  Credential Manager
        Linux    →  Secret Service / libsecret

    Returning ``None`` indicates "key not yet provisioned"; the GUI must
    prompt the student before any LLM call.
    """

    def __init__(self, invoke_fn: Callable[[str, dict], str | None]) -> None:
        self._invoke = invoke_fn

    def get_secret(self, name: str) -> str | None:
        return self._invoke("secret_get", {"name": name})

    def set_secret(self, name: str, value: str) -> None:
        self._invoke("secret_set", {"name": name, "value": value})

    def delete_secret(self, name: str) -> None:
        self._invoke("secret_delete", {"name": name})

    def list_aliases(self) -> Iterable[str]:
        result = self._invoke("secret_list", {})
        if result is None:
            return []
        return json.loads(result) if isinstance(result, str) else list(result)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# 2. Encrypted file fallback
# --------------------------------------------------------------------------- #
PBKDF2_ITERATIONS = 600_000
SALT_BYTES = 16


class EncryptedFileStore(SecurityStore):
    """Passphrase-derived Fernet store. Suitable for Linux fallback + tests."""

    def __init__(self, *, path: Path, passphrase: str) -> None:
        self._path = Path(path)
        self._fernet = self._derive(passphrase)
        self._cache: dict[str, str] = {}
        self._load()

    @staticmethod
    def _kdf(passphrase: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))

    def _derive(self, passphrase: str) -> Fernet:
        if self._path.exists():
            payload = json.loads(self._path.read_text("utf-8"))
            salt = base64.b64decode(payload["salt"])
        else:
            salt = secrets.token_bytes(SALT_BYTES)
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps({"salt": base64.b64encode(salt).decode(), "items": {}}),
                encoding="utf-8",
            )
        return Fernet(self._kdf(passphrase, salt))

    def _load(self) -> None:
        payload = json.loads(self._path.read_text("utf-8"))
        items = payload.get("items", {})
        decrypted: dict[str, str] = {}
        for name, token in items.items():
            try:
                decrypted[name] = self._fernet.decrypt(token.encode("utf-8")).decode("utf-8")
            except InvalidToken as exc:
                raise PermissionError(
                    "Wrong passphrase for the encrypted key store."
                ) from exc
        self._cache = decrypted

    def _flush(self) -> None:
        payload = json.loads(self._path.read_text("utf-8"))
        payload["items"] = {
            name: self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")
            for name, value in self._cache.items()
        }
        self._path.write_text(json.dumps(payload), encoding="utf-8")
        try:
            os.chmod(self._path, 0o600)
        except OSError:  # noqa: S110 - Windows / sandboxed FS may refuse chmod.
            pass

    def get_secret(self, name: str) -> str | None:
        return self._cache.get(name)

    def set_secret(self, name: str, value: str) -> None:
        self._cache[name] = value
        self._flush()

    def delete_secret(self, name: str) -> None:
        self._cache.pop(name, None)
        self._flush()

    def list_aliases(self) -> Iterable[str]:
        return list(self._cache.keys())


# --------------------------------------------------------------------------- #
# 3. Null store (server build)
# --------------------------------------------------------------------------- #
class NullStore(SecurityStore):
    """No-op store; raises on writes so server builds fail loudly if misrouted."""

    def get_secret(self, name: str) -> str | None:
        return None

    def set_secret(self, name: str, value: str) -> None:
        raise RuntimeError("NullStore is read-only; cannot store local API keys here.")

    def delete_secret(self, name: str) -> None:
        raise RuntimeError("NullStore is read-only.")

    def list_aliases(self) -> Iterable[str]:
        return []


# --------------------------------------------------------------------------- #
# Selector
# --------------------------------------------------------------------------- #
def build_default_store(
    *,
    mode: str = "server",
    fallback_path: Path | None = None,
    fallback_passphrase: str | None = None,
    tauri_invoke: Callable[[str, dict], str | None] | None = None,
) -> SecurityStore:
    """Pick the right store for the runtime.

    Parameters
    ----------
    mode
        ``"server"`` returns :class:`NullStore`. ``"desktop"`` prefers
        :class:`TauriKeyringStore`, falls back to :class:`EncryptedFileStore`.
    """
    if mode == "server":
        return NullStore()
    if mode == "desktop":
        if tauri_invoke is not None:
            return TauriKeyringStore(invoke_fn=tauri_invoke)
        if fallback_path is None or fallback_passphrase is None:
            raise ValueError(
                "Desktop build without Tauri bridge requires fallback_path and "
                "fallback_passphrase to be provided."
            )
        return EncryptedFileStore(path=fallback_path, passphrase=fallback_passphrase)
    raise ValueError(f"Unknown store mode: {mode}")
