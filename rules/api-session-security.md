# api-session-security

> Use opaque server-side sessions, rotate identifiers on privilege change, and enforce secure cookie policy

## Why It Matters

A session identifier is a bearer credential. Whoever presents it inherits the
session's authority. Storing authentication state under ad-hoc string keys,
reusing an anonymous identifier after login, or accepting a long-lived cookie
without transport and cross-site policy enables fixation, theft, and accidental
authorization bypass.

## Contract

- Store only an opaque, high-entropy identifier in the browser; keep
  authoritative session state server-side for revocation and bounded size.
- Rotate the identifier after login, privilege elevation, password change, and
  other trust-boundary transitions.
- Invalidate the server-side session on logout and sensitive credential
  changes.
- Set `Secure`, `HttpOnly`, an intentional `SameSite` value, a narrow `Path`,
  and no broader `Domain` than required.
- Use idle and absolute expirations. Enforce them in the server-side store,
  not only through the browser cookie.
- Authenticate first and authorize every protected operation against current
  server-side state.
- Wrap framework session access in a typed API so keys and value types cannot
  drift across handlers.
- Treat serialization, store, and revocation failures as real errors.

## Bad

```rust
pub fn login(session: &mut Session, user_id: String) {
    // Keeps the attacker-seeded identifier and a stringly key.
    session.insert("user", user_id);
}
```

## Good

```text
login succeeds
  -> invalidate anonymous session identifier
  -> create a fresh authenticated session
  -> persist user/tenant/expiry in the server-side store
  -> return a Secure + HttpOnly + SameSite cookie
```

## Failure Tests

- a pre-login identifier is unusable after successful login;
- logout revokes the server record;
- expired sessions fail even when the client replays the cookie;
- missing, malformed, and store-unavailable sessions fail closed;
- cookie attributes are asserted through a black-box HTTP test.

## See Also

- [api-extract-or-reject](api-extract-or-reject.md) - reject malformed credentials before handlers
- [test-http-blackbox](test-http-blackbox.md) - verify cookie and redirect behavior
- [obs-no-sensitive-data](obs-no-sensitive-data.md) - never record session identifiers
- [proj-typed-config](proj-typed-config.md) - inject signing/encryption keys and store settings
- [err-edge-mapping](err-edge-mapping.md) - keep internal session failures out of responses
