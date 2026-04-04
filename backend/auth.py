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
) -> dict[str, Any] | None:
    auth_settings = get_auth_settings()
    if not auth_settings["enabled"]:
        return None

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Auth0 access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Auth0 token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc