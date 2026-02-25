"""Authentication and token management for zpools.io API."""
import os
import json
import time
from pathlib import Path
from typing import Optional

from ._generated import Client


class AuthManager:
    """Manages authentication tokens (JWT and PAT) for zpools.io API."""

    def __init__(
        self,
        api_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        pat: Optional[str] = None,
        token_cache_dir: Optional[str] = None,
    ):
        """
        Initialize authentication manager.
        
        Args:
            api_url: API base URL
            username: Username for JWT authentication
            password: Password for JWT authentication
            pat: Personal Access Token (alternative to JWT)
            token_cache_dir: Base directory for JWT token cache. If unset or empty,
                JWT tokens are not cached (most secure). Set explicitly to enable caching.
        """
        self.api_url = api_url
        self.username = username
        self.password = password
        self.pat = pat
        # Only cache when explicitly set; unset or empty means no cache (secure default)
        resolved = (token_cache_dir or "").strip()
        self._token_cache_dir = resolved if resolved else ""

        if self.username and " " in self.username:
            raise ValueError("Username must not contain spaces.")
        if not self.username and not self.pat:
            raise ValueError("Username or PAT is required.")
        
        self._raw_client = Client(base_url=self.api_url)
        self._token_file = self._get_token_file_path() if (self.username and self._token_cache_dir) else None
    
    def set_password(self, password: str):
        """Set the password for login if not provided during init."""
        self.password = password
    
    def _get_token_file_path(self) -> Path:
        """Determine path for caching JWT tokens (ephemeral, not persisted to disk)."""
        if not self.username:
            raise ValueError("Username is required to determine token cache path.")
        if " " in self.username:
            raise ValueError("Username must not contain spaces.")
        domain_clean = self.api_url.replace("https://", "").replace("http://", "").split("/")[0]
        user_safe = self.username
        base_dir = Path(self._token_cache_dir)
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / f"zpool_token_{domain_clean}_{user_safe}"
    
    def _get_cached_token(self) -> Optional[str]:
        """Retrieve valid access token from cache if it exists and isn't expired."""
        if self._token_file is None or not self._token_file.exists():
            return None
            
        try:
            data = json.loads(self._token_file.read_text())
            expires_at = data.get("expires_at", 0)
            if time.time() < expires_at:
                return data.get("access_token")
        except Exception:
            return None
        return None
    
    def _login(self) -> str:
        """Perform login to get new JWT tokens (direct HTTP; not in published spec)."""
        if not self.username or not self.password:
            raise ValueError("Username and password are required for login.")

        url = f"{self.api_url.rstrip('/')}/login"
        payload = {"username": self.username, "password": self.password}
        response = self._raw_client.get_httpx_client().post(url, json=payload)

        if response.status_code not in (200, 201):
            try:
                detail = response.json().get("message", "")
            except Exception:
                detail = ""
            raise RuntimeError(f"Login failed (HTTP {response.status_code}): {detail or 'authentication failed'}")

        data = response.json()
        detail = data.get("detail") or {}
        access_token = detail.get("access_token")
        id_token = detail.get("id_token")
        expires_in = int(detail.get("expires_in", 0))
        if not access_token:
            raise RuntimeError("Login response missing access_token")
        expires_at = int(time.time()) + expires_in
        
        # Cache tokens (only if cache is enabled)
        if self._token_file is not None:
            token_data = {
                "access_token": access_token,
                "id_token": id_token,
                "expires_at": expires_at
            }
            self._token_file.parent.mkdir(parents=True, exist_ok=True)
            self._token_file.touch(mode=0o600)
            self._token_file.write_text(json.dumps(token_data))
        
        return access_token
    
    def get_token(self) -> str:
        """
        Get a valid authentication token.
        Priority:
        1. PAT (if configured)
        2. Cached JWT (if valid)
        3. New JWT (via login)
        """
        if self.pat:
            return self.pat
            
        token = self._get_cached_token()
        if token:
            return token
            
        return self._login()
    
    def get_authenticated_client(self):
        """Returns an AuthenticatedClient with the Authorization header set."""
        from ._generated import AuthenticatedClient
        
        token = self.get_token()
        return AuthenticatedClient(
            base_url=self.api_url,
            token=token
        )
