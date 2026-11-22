import json
import logging
from collections.abc import Generator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from careeros_identity.adapters.http import CORRELATION_HEADER, Settings, create_app


@contextmanager
def client() -> Generator[TestClient]:
    settings = Settings(
        app_env="test",
        log_level="info",
        oidc_issuer="https://identity.example.invalid/realms/careeros",
        oidc_audience="careeros-api",
        oidc_jwks_url="https://identity.example.invalid/jwks",
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.mark.parametrize(("path", "status"), [("/health", "ok"), ("/ready", "ready")])
def test_operational_endpoints(path: str, status: str) -> None:
    with client() as test_client:
        response = test_client.get(path)

    assert response.status_code == 200
    assert response.json() == {"status": status, "service": "identity-service"}
    assert response.headers[CORRELATION_HEADER]


def test_preserves_safe_correlation_id_without_exposing_configuration() -> None:
    with client() as test_client:
        response = test_client.get("/ready", headers={CORRELATION_HEADER: "test-request-42"})

    assert response.headers[CORRELATION_HEADER] == "test-request-42"
    assert "test" not in response.text
    assert "log_level" not in response.text


def test_structured_logs_redact_query_values(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="careeros.identity.http"), client() as test_client:
        test_client.get("/ready?token=do-not-log", headers={CORRELATION_HEADER: "log-test-7"})

    payload = json.loads(caplog.records[-1].message)
    assert payload == {
        "correlation_id": "log-test-7",
        "event": "http_request",
        "method": "GET",
        "path": "/ready",
        "status_code": 200,
    }
    assert "do-not-log" not in caplog.text


def test_rejects_invalid_startup_configuration() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate(
            {
                "app_env": "staging",
                "log_level": "info",
                "oidc_issuer": "https://identity.example.invalid/realms/careeros",
                "oidc_audience": "careeros-api",
                "oidc_jwks_url": "https://identity.example.invalid/jwks",
            }
        )

    with pytest.raises(ValidationError):
        Settings.model_validate({})


def test_openapi_documents_public_operational_endpoints() -> None:
    with client() as test_client:
        document = test_client.get("/openapi.json").json()

    assert {"/health", "/ready"}.issubset(document["paths"])
