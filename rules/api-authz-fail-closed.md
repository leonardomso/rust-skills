# api-authz-fail-closed

> Authenticate the principal, authorize the operation, and deny access unless both decisions succeed

## Why It Matters

Authentication answers who is calling; authorization answers whether that
principal may perform this operation on this resource. A valid session is not
permission to every route. Missing middleware, backend errors, or unknown
policy results must not turn into access.

## Contract

- Authenticate credentials at a trusted ingress and construct a typed
  principal; handlers do not parse raw credentials repeatedly.
- Authorize every protected operation against principal, action, resource, and
  current tenant/state.
- Default to deny for missing policy, indeterminate results, and authorization
  service failures.
- Keep checks near the operation or in a mandatory policy layer that cannot be
  bypassed by registering a route differently.
- Distinguish unauthenticated from authenticated-but-forbidden without leaking
  whether another tenant's resource exists.
- Use least-privilege service identities for downstream calls.
- Record decision metadata and policy version without credentials or sensitive
  resource data.

## Bad

```rust
pub async fn delete_user(session: Session, target: UserId) {
    assert!(session.user_id().is_some());
    database.delete(target).await;
}
```

## Good

```rust
pub struct UserId(pub u64);
pub struct TenantId(pub u64);

pub struct Principal {
    pub user_id: UserId,
    pub tenant_id: TenantId,
}

pub enum Decision {
    Allow,
    Deny,
    Indeterminate,
}

#[derive(Debug)]
pub struct Forbidden;

pub fn require(decision: Decision) -> Result<(), Forbidden> {
    match decision {
        Decision::Allow => Ok(()),
        Decision::Deny | Decision::Indeterminate => Err(Forbidden),
    }
}

fn main() {
    assert!(require(Decision::Deny).is_err());
    assert!(require(Decision::Indeterminate).is_err());
}
```

## Failure Tests

- missing, expired, malformed, and revoked credentials fail closed;
- a valid principal without the required permission is denied;
- cross-tenant identifiers do not reveal resource existence;
- policy/backend timeout is denied, not treated as anonymous or allowed;
- every protected route appears in an authorization coverage test.

## See Also

- [api-session-security](api-session-security.md) - establish and rotate the authenticated session
- [api-password-auth](api-password-auth.md) - authenticate password credentials safely
- [api-extract-or-reject](api-extract-or-reject.md) - parse credentials at the boundary
- [err-edge-mapping](err-edge-mapping.md) - map denial without leaking internals
- [obs-no-sensitive-data](obs-no-sensitive-data.md) - keep credentials out of decision telemetry
