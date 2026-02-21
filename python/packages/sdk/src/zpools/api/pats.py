"""Personal Access Token (PAT) operations."""

from types import SimpleNamespace


class PATMixin:
    """Mixin providing PAT management operations."""
    
    def create_pat(self, label: str, scopes: list = None, expiry: str = None, tenant_id: str = None):
        """
        Create a Personal Access Token (direct HTTP; not in published spec).
        
        Args:
            label: Human-readable label for the PAT
            scopes: Optional list of scopes (e.g., ['pat', 'sshkey', 'job', 'zpool'])
            expiry: Optional expiry date (YYYY-MM-DD)
            tenant_id: Optional tenant ID
            
        Returns:
            Response with status_code, detail.key_id, and detail.token
        """
        auth_client = self._auth.get_authenticated_client()
        body = {"label": label}
        if scopes is not None:
            body["scopes"] = scopes
        if expiry is not None:
            body["expiry"] = expiry if isinstance(expiry, str) else expiry.isoformat()
        if tenant_id is not None:
            body["tenant_id"] = tenant_id

        base = auth_client._base_url.rstrip("/")
        response = auth_client.get_httpx_client().post(f"{base}/pat", json=body)
        data = response.json() if response.content else {}
        detail = data.get("detail") or {}
        parsed = SimpleNamespace(detail=SimpleNamespace(key_id=detail.get("key_id"), token=detail.get("token")))
        return SimpleNamespace(status_code=response.status_code, content=response.content, parsed=parsed)
    
    def list_pats(self):
        """
        List all Personal Access Tokens.
        
        Returns:
            Response with status_code and parsed list of PATs
        """
        from .._generated.api.personal_access_tokens import get_pat
        
        auth_client = self._auth.get_authenticated_client()
        return get_pat.sync_detailed(client=auth_client)
    
    def revoke_pat(self, key_id: str):
        """
        Revoke a Personal Access Token.
        
        Args:
            key_id: The key_id of the PAT to revoke
            
        Returns:
            Response with status_code
        """
        from .._generated.api.personal_access_tokens import delete_pat_key_id
        
        auth_client = self._auth.get_authenticated_client()
        return delete_pat_key_id.sync_detailed(client=auth_client, key_id=key_id)
