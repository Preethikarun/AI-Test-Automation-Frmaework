"""
api/auth_handler.py

Handles all authentication types for APIClient.
Auth config comes from the definition JSON — never hardcoded.

Supported types:
  none     — no auth
  apikey   — API key in header or query param
  bearer   — Bearer token in Authorization header
  basic    — HTTP Basic auth (username:password)
  oauth2   — Client credentials flow (token refresh included)
  cert     — mTLS client certificate

All credentials loaded from .env via environment variables.
Definition JSON references env vars by name, e.g.:
  "auth": {"type": "bearer", "token_env": "MY_API_TOKEN"}

Usage:
    handler = AuthHandler.from_definition(auth_config)
    headers = handler.get_headers()
"""

from __future__ import annotations

import base64
import os
import time
from typing import Optional


class AuthHandler:
    """
    Builds auth headers / params for a single API request.
    Instantiated once per APIClient session and reused.
    """

    def __init__(self, auth_type: str = "none", **kwargs):
        self.auth_type = auth_type.lower()
        self._config   = kwargs
        self._token:   Optional[str] = None
        self._token_expiry: float    = 0.0

    # ── factory ───────────────────────────────────────────────────

    @classmethod
    def from_definition(cls, auth: dict) -> "AuthHandler":
        """
        Build AuthHandler from a test definition auth block.

        Example definition blocks:
          {"type": "none"}
          {"type": "bearer",  "token_env": "MY_TOKEN"}
          {"type": "apikey",  "key_env": "MY_KEY", "header": "X-Api-Key"}
          {"type": "basic",   "user_env": "MY_USER", "pass_env": "MY_PASS"}
          {"type": "oauth2",  "token_url": "...", "client_id_env": "...",
                              "client_secret_env": "..."}
        """
        if not auth:
            return cls(auth_type="none")
        return cls(auth_type=auth.get("type", "none"), **auth)

    # ── public interface ──────────────────────────────────────────

    def get_headers(self) -> dict:
        """Return auth headers to merge into the request."""
        if self.auth_type == "none":
            return {}
        if self.auth_type == "bearer":
            return {"Authorization": f"Bearer {self._bearer_token()}"}
        if self.auth_type == "basic":
            return {"Authorization": f"Basic {self._basic_token()}"}
        if self.auth_type == "oauth2":
            return {"Authorization": f"Bearer {self._oauth2_token()}"}
        if self.auth_type == "apikey":
            header = self._config.get("header", "X-Api-Key")
            return {header: self._env("key_env")}
        if self.auth_type == "cert":
            return {}   # cert passed as httpx cert= param, not a header
        raise ValueError(f"Unknown auth type: {self.auth_type}")

    def get_params(self) -> dict:
        """Return auth query params (apikey in query string mode)."""
        if self.auth_type == "apikey" and self._config.get("in") == "query":
            param = self._config.get("param", "api_key")
            return {param: self._env("key_env")}
        return {}

    def get_cert(self) -> Optional[tuple]:
        """Return (cert_path, key_path) tuple for mTLS."""
        if self.auth_type == "cert":
            return (
                self._env("cert_path_env"),
                self._env("key_path_env"),
            )
        return None

    # ── auth implementations ──────────────────────────────────────

    def _bearer_token(self) -> str:
        return self._env("token_env")

    def _basic_token(self) -> str:
        user     = self._env("user_env")
        password = self._env("pass_env")
        return base64.b64encode(
            f"{user}:{password}".encode()
        ).decode()

    def _oauth2_token(self) -> str:
        """
        Client credentials flow with automatic token refresh.
        Token is cached until expiry to avoid re-fetching on every call.
        """
        if self._token and time.time() < self._token_expiry:
            return self._token

        import httpx  # lazy import — only needed for oauth2

        token_url     = self._config.get("token_url", "")
        client_id     = self._env("client_id_env")
        client_secret = self._env("client_secret_env")
        scope         = self._config.get("scope", "")

        response = httpx.post(
            token_url,
            data={
                "grant_type":    "client_credentials",
                "client_id":     client_id,
                "client_secret": client_secret,
                "scope":         scope,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        self._token        = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 3600) - 30
        return self._token

    # ── env var helper ────────────────────────────────────────────

    def _env(self, key: str) -> str:
        """
        Read credential from environment variable.
        The definition JSON stores env var names, not values.
        """
        env_var_name = self._config.get(key, "")
        value        = os.getenv(env_var_name, "")
        if not value:
            raise EnvironmentError(
                f"Auth: environment variable '{env_var_name}' "
                f"is not set. Add it to your .env file."
            )
        return value
