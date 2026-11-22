from uuid import UUID

import pytest
from pydantic import ValidationError

from careeros_identity.application.authentication import AccountContext
from careeros_identity.application.authorization import (
    AuthorizationDenial,
    AuthorizationDenied,
    AuthorizationPolicy,
    OwnedTarget,
    TenantTarget,
)

ACCOUNT_ID = UUID("00000000-0000-4000-8000-000000000001")
OTHER_ACCOUNT_ID = UUID("00000000-0000-4000-8000-000000000003")
TENANT_ID = UUID("00000000-0000-4000-8000-000000000002")
OTHER_TENANT_ID = UUID("00000000-0000-4000-8000-000000000004")


def account_context() -> AccountContext:
    return AccountContext(
        account_id=ACCOUNT_ID,
        tenant_id=TENANT_ID,
        roles=("admin",),
        scopes=("identity:write",),
    )


def test_allows_access_to_same_tenant() -> None:
    policy = AuthorizationPolicy()

    policy.require_tenant_access(account_context(), TenantTarget(tenant_id=TENANT_ID))


def test_allows_owner_in_same_tenant() -> None:
    policy = AuthorizationPolicy()

    policy.require_ownership(
        account_context(),
        OwnedTarget(tenant_id=TENANT_ID, owner_account_id=ACCOUNT_ID),
    )


def test_denies_tenant_scoped_access_across_tenants() -> None:
    policy = AuthorizationPolicy()

    with pytest.raises(AuthorizationDenied) as denied:
        policy.require_tenant_access(account_context(), TenantTarget(tenant_id=OTHER_TENANT_ID))

    assert denied.value.reason is AuthorizationDenial.TENANT_MISMATCH


def test_denies_access_across_tenants_even_when_account_matches() -> None:
    policy = AuthorizationPolicy()
    target = OwnedTarget(tenant_id=OTHER_TENANT_ID, owner_account_id=ACCOUNT_ID)

    with pytest.raises(AuthorizationDenied) as denied:
        policy.require_ownership(account_context(), target)

    assert denied.value.reason is AuthorizationDenial.TENANT_MISMATCH
    assert str(denied.value) == "access denied"


def test_denies_non_owner_even_with_admin_role_and_write_scope() -> None:
    policy = AuthorizationPolicy()
    target = OwnedTarget(tenant_id=TENANT_ID, owner_account_id=OTHER_ACCOUNT_ID)

    with pytest.raises(AuthorizationDenied) as denied:
        policy.require_ownership(account_context(), target)

    assert denied.value.reason is AuthorizationDenial.OWNERSHIP_MISMATCH


def test_rejects_invalid_authorization_target() -> None:
    with pytest.raises(ValidationError):
        OwnedTarget.model_validate(
            {
                "tenant_id": "not-a-uuid",
                "owner_account_id": str(ACCOUNT_ID),
                "unexpected": True,
            }
        )
