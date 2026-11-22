from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends
from fastapi.testclient import TestClient
from jwt import PyJWK

from careeros_identity.adapters.auth import JwtTokenVerifier
from careeros_identity.adapters.http import Settings, create_app, require_account_context
from careeros_identity.application import AccountContext, TokenValidationError

ACCOUNT_ID = UUID("00000000-0000-4000-8000-000000000001")
TENANT_ID = UUID("00000000-0000-4000-8000-000000000002")


class StaticResolver:
    def __init__(self, key: PyJWK) -> None:
        self._key = key

    def resolve(self, token: str) -> PyJWK:
        return self._key


def settings() -> Settings:
    return Settings(
        app_env="test",
        log_level="error",
        oidc_issuer="https://identity.example.invalid/realms/careeros",
        oidc_audience="careeros-api",
        oidc_jwks_url="https://identity.example.invalid/jwks",
    )


def token_verifier() -> tuple[JwtTokenVerifier, rsa.RSAPrivateKey]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk = PyJWK.from_json(jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key()))
    return JwtTokenVerifier(
        resolver=StaticResolver(public_jwk),
        issuer=str(settings().oidc_issuer),
        audience=settings().oidc_audience,
    ), private_key


def token(private_key: rsa.RSAPrivateKey, **overrides: object) -> str:
    now = datetime.now(UTC)
    claims: dict[str, object] = {
        "aud": "careeros-api",
        "exp": now + timedelta(minutes=5),
        "iat": now,
        "iss": "https://identity.example.invalid/realms/careeros",
        "realm_access": {"roles": ["member", "member", "admin"]},
        "scope": "profile:read profile:read applications:write",
        "sub": str(ACCOUNT_ID),
        "tenant_id": str(TENANT_ID),
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "test-key"})


def test_validates_and_normalizes_identity_claims() -> None:
    verifier, private_key = token_verifier()

    context = verifier.verify(token(private_key))

    assert context == AccountContext(
        account_id=ACCOUNT_ID,
        tenant_id=TENANT_ID,
        roles=("admin", "member"),
        scopes=("applications:write", "profile:read"),
    )


@pytest.mark.parametrize("overrides", [{"aud": "other"}, {"tenant_id": None}, {"exp": 0}])
def test_rejects_untrusted_or_incomplete_tokens(overrides: dict[str, object]) -> None:
    verifier, private_key = token_verifier()

    with pytest.raises(TokenValidationError):
        verifier.verify(token(private_key, **overrides))


def test_rejects_token_signed_by_an_untrusted_key() -> None:
    verifier, _ = token_verifier()
    untrusted_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    with pytest.raises(TokenValidationError):
        verifier.verify(token(untrusted_key))


def test_http_dependency_exposes_context_and_denies_missing_token() -> None:
    verifier, private_key = token_verifier()
    application = create_app(settings(), verifier)

    @application.get("/test-only/context")
    def protected(
        context: Annotated[AccountContext, Depends(require_account_context)],
    ) -> AccountContext:
        return context

    with TestClient(application) as client:
        denied = client.get("/test-only/context")
        allowed = client.get(
            "/test-only/context", headers={"Authorization": f"Bearer {token(private_key)}"}
        )

    assert denied.status_code == 401
    assert denied.json() == {"detail": {"code": "UNAUTHENTICATED"}}
    assert denied.headers["WWW-Authenticate"] == "Bearer"
    assert allowed.status_code == 200
    assert allowed.json()["tenant_id"] == str(TENANT_ID)
