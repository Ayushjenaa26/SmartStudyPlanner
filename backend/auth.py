import os
from functools import lru_cache
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer_scheme = HTTPBearer(auto_error=False)


def _normalize_domain(domain: str) -> str:
    domain = domain.strip()
    if domain.startswith("https://"):
        domain = domain[len("https://") :]
    elif domain.startswith("http://"):
        domain = domain[len("http://") :]
    return domain.rstrip("/")


def get_auth_settings() -> dict[str, Any]:
    domain = _normalize_domain(os.getenv("AUTH0_DOMAIN", ""))
    client_id = os.getenv("AUTH0_CLIENT_ID", "").strip()
    audience = os.getenv("AUTH0_AUDIENCE", "").strip() or client_id
    issuer = os.getenv("AUTH0_ISSUER", f"https://{domain}/" if domain else "").strip()
    redirect_uri = os.getenv("AUTH0_REDIRECT_URI", "").strip()

    enabled = bool(domain and client_id)

    return {
        "enabled": enabled,
        "domain": domain,
        "clientId": client_id,
        "audience": audience,
        "issuer": issuer,
        "redirectUri": redirect_uri,
    }


@lru_cache(maxsize=1)
def _get_jwks_client(domain: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(f"https://{domain}/.well-known/jwks.json")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    """Get current user from auth token. Raises 401 if no valid credentials provided."""
    auth_settings = get_auth_settings()
    
    # If auth is not configured, allow guest access (return empty dict)
    if not auth_settings["enabled"]:
        return {}
    
    # If no credentials provided, raise 401
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    domain = auth_settings["domain"]
    audience = auth_settings["audience"]
    issuer = auth_settings["issuer"] or f"https://{domain}/"

    try:
        signing_key = _get_jwks_client(domain).get_signing_key_from_jwt(credentials.credentials).key
        payload = jwt.decode(
            credentials.credentials,
            signing_key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
        )
        return payload
    except Exception as exc:
        # Invalid or expired token
        print(f"Auth token validation failed: {exc}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")