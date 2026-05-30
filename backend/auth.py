import os
import json
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
    """Get current user from auth token. Returns None if no valid credentials provided (guest mode)."""
    auth_settings = get_auth_settings()
    
    # If auth is not configured, allow guest access (return None for guest mode)
    if not auth_settings["enabled"]:
        return None
    
    # If no credentials provided, return None for guest/demo mode
    if credentials is None or not credentials.credentials:
        return None

    token = credentials.credentials
    
    # Check for demo mode token (signature is "demo_signature")
    if token.endswith(".demo_signature"):
        try:
            import base64
            # Demo token format: header.payload.demo_signature
            parts = token.split(".")
            if len(parts) == 3:
                # Decode the payload (add padding if needed)
                payload_str = parts[1]
                padding = 4 - len(payload_str) % 4
                if padding != 4:
                    payload_str += "=" * padding
                payload_json = base64.urlsafe_b64decode(payload_str)
                payload = json.loads(payload_json)
                # Verify expiry
                now = int(__import__('time').time())
                if payload.get('exp', 0) > now:
                    return payload
        except Exception as e:
            print(f"Demo token validation failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid demo token")

    domain = auth_settings["domain"]
    audience = auth_settings["audience"]
    issuer = auth_settings["issuer"] or f"https://{domain}/"

    try:
        signing_key = _get_jwks_client(domain).get_signing_key_from_jwt(token).key
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
            leeway=120,  # Allow clock skew for freshly issued tokens
            options={
                "verify_iat": False,  # iat is informational; don't block immediate post-login requests
            },
        )
        return payload
    except Exception as exc:
        # Invalid or expired token
        print(f"Auth token validation failed: {exc}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")