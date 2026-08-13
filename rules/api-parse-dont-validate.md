# api-parse-dont-validate

> Convert boundary data into types that preserve local invariants

## Why It Matters

Repeatedly checking raw strings and integers lets callers forget a required condition. A private representation plus a fallible constructor can ensure every value satisfies stable, context-free invariants such as non-empty, bounded length, allowed syntax, or non-zero. It cannot permanently prove facts that depend on time, authorization, DNS, database state, revocation, or another service. Name and document exactly which invariants the type preserves.

## Bad

```rust
fn create_user(raw_name: String) -> Result<User, Error> {
    if raw_name.is_empty() {
        return Err(Error::EmptyName);
    }
    // A later path can still construct/store unchecked String values.
    Ok(User { name: raw_name })
}
```

## Good

```rust
use std::fmt;

pub struct UserName(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum UserNameError {
    Empty,
    TooLong,
    InvalidCharacter,
}

impl UserName {
    pub const MAX_BYTES: usize = 64;

    pub fn parse(raw: String) -> Result<Self, UserNameError> {
        if raw.is_empty() {
            return Err(UserNameError::Empty);
        }
        if raw.len() > Self::MAX_BYTES {
            return Err(UserNameError::TooLong);
        }
        if !raw.chars().all(|c| c.is_alphanumeric() || matches!(c, '-' | '_')) {
            return Err(UserNameError::InvalidCharacter);
        }
        Ok(Self(raw))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl fmt::Debug for UserName {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_tuple("UserName").field(&"[redacted]").finish()
    }
}
```

The private field prevents unchecked construction outside the module. Mutation APIs must preserve the same constraints; omitting `DerefMut` and direct inner access is part of the contract. Redact user data when `Debug` may reach logs.

## Numeric Invariants

```rust
use std::num::NonZeroU16;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Port(NonZeroU16);

impl TryFrom<u16> for Port {
    type Error = ZeroPort;

    fn try_from(value: u16) -> Result<Self, Self::Error> {
        NonZeroU16::new(value).map(Self).ok_or(ZeroPort)
    }
}

impl From<Port> for u16 {
    fn from(value: Port) -> Self {
        value.0.get()
    }
}
```

Use standard invariant-bearing types when they fit. A port newtype proves only non-zero numeric range; it does not prove that the port is available, permitted, or bound.

## Boundary Conversion Before Effects

```rust
pub struct CreateUser {
    pub name: UserName,
    pub age: Age,
}

fn extract(raw: RawRequest) -> Result<CreateUser, BadRequest> {
    let name = UserName::parse(raw.name).map_err(BadRequest::Name)?;
    let age = Age::try_from(raw.age).map_err(BadRequest::Age)?;
    Ok(CreateUser { name, age })
}

async fn handle(raw: RawRequest, service: &UserService) -> Result<Response, ApiError> {
    let command = extract(raw)?; // No database/message side effects before this succeeds.
    service.create(command).await.map(Response::created)
}
```

Bound body size, collection count, nesting, and decode work before or during extraction. Map internal parse detail to stable public errors and keep sensitive values out of diagnostics.

## Contextual And Time-Varying Validity

Do not encode `AuthorizedUser`, `ReachableEmail`, or `AvailableName` as if construction made those facts permanent. Carry evidence with a scope and freshness boundary, or re-check at the decision point:

```rust
async fn delete_project(
    actor: &Principal,
    project: ProjectId,
    policy: &PolicyClient,
) -> Result<(), Error> {
    policy.authorize(actor, Action::Delete, project).await?;
    delete_authorized(project).await
}
```

Authorization fails closed when the policy decision is unavailable or indeterminate. A validated identifier does not imply permission.

## Serde And Database Boundaries

Deriving `Deserialize` directly on a private-field newtype can bypass a fallible constructor depending on the implementation. Deserialize through `TryFrom`, a custom visitor, or a raw DTO conversion and test invalid cases. Database reads can contain legacy/corrupt values; decode them fallibly rather than using an unchecked constructor.

Compile-time SQL macros validate syntax/types against the schema information supplied at build time. They do not prove production schema freshness, authorization, transaction semantics, cardinality, query cost, or result existence. Keep migration admission and runtime error handling.

## API Checklist

- State the exact invariant and units (`bytes` versus Unicode scalar values/graphemes).
- Keep the representation private and expose only invariant-preserving operations.
- Define normalization and canonicalization deliberately; do not silently alter security-sensitive identifiers.
- Avoid `Display`, `Debug`, `Serialize`, or error messages that leak secrets or PII.
- Use `TryFrom`/`FromStr` when those standard conversion contracts fit.
- Test empty, boundary, oversized, malformed, Unicode, and round-trip cases.
- Revalidate contextual facts at the effect boundary.

## See Also

- [type-newtype-validated](type-newtype-validated.md) - preserve constructor invariants
- [api-extract-or-reject](api-extract-or-reject.md) - reject untrusted input before effects
- [api-authz-fail-closed](api-authz-fail-closed.md) - re-check contextual authorization
- [serde-try-from-validate](serde-try-from-validate.md) - prevent deserialization bypass
