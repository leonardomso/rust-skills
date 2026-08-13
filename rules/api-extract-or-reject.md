# api-extract-or-reject

> Parse and validate transport input before handler logic; reject malformed requests without side effects

## Why It Matters

Handlers that accept strings and inspect them mid-operation can write partial
state before discovering malformed input. The transport adapter should decode
path, query, headers, and body into typed request values first. Conversion
failure returns a stable client error and the application operation never
starts.

## Bad

```rust
pub async fn subscribe(email: String, store: &Store) -> Result<(), Error> {
    store.reserve_slot().await?;
    if !email.contains('@') {
        return Err(Error::InvalidEmail);
    }
    store.insert(email).await
}
```

## Good

```rust
#[derive(Debug)]
pub struct RawSubscribe {
    pub email: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SubscriberEmail(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BadRequest {
    InvalidEmail,
}

impl TryFrom<RawSubscribe> for SubscriberEmail {
    type Error = BadRequest;

    fn try_from(raw: RawSubscribe) -> Result<Self, Self::Error> {
        if raw.email.len() > 254 {
            return Err(BadRequest::InvalidEmail);
        }
        let (local, domain) = raw
            .email
            .split_once('@')
            .ok_or(BadRequest::InvalidEmail)?;
        if local.is_empty() || domain.is_empty() || domain.contains('@') {
            return Err(BadRequest::InvalidEmail);
        }
        Ok(Self(raw.email))
    }
}

pub struct SubscribeRequest {
    pub email: SubscriberEmail,
}

fn main() {
    let email = SubscriberEmail::try_from(RawSubscribe {
        email: "user@example.com".to_owned(),
    })
    .expect("literal contains a non-empty local and domain");
    let _ = SubscribeRequest { email };
}
```

The framework extractor first enforces media type, body-size, required-field,
and unknown-field policy. It then invokes the transport-to-domain conversion.
Only `SubscribeRequest` reaches the application service; the edge maps
`BadRequest::InvalidEmail` to a stable public 4xx message rather than exposing
parser internals.

## Contract

- Distinguish malformed transport syntax from a well-formed domain command
  that conflicts with current state.
- Reject missing, unknown, or oversized input according to the API contract.
- Return a stable 4xx response without leaking parser/library internals.
- Do not perform database, queue, or network effects until extraction and
  validation succeed.
- Property tests exercise accepted and rejected boundaries; black-box tests
  prove invalid payloads leave persistent state unchanged.

## See Also

- [api-parse-dont-validate](api-parse-dont-validate.md) - make the parsed type carry the invariant
- [type-newtype-validated](type-newtype-validated.md) - keep invalid values unconstructible
- [serde-rename-all](serde-rename-all.md) - define field casing at the wire boundary
- [serde-deny-unknown-fields](serde-deny-unknown-fields.md) - choose whether unknown input is rejected
- [test-proptest-properties](test-proptest-properties.md) - generate boundary cases
- [test-http-blackbox](test-http-blackbox.md) - prove rejection has no effects
