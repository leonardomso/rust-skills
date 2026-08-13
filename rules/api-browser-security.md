# api-browser-security

> Escape untrusted output, protect state-changing browser requests from CSRF, and authenticate redirect state

## Why It Matters

Input validation does not make text safe for HTML, JavaScript, URLs, SQL, or
headers. The correct transformation depends on the output context. Browsers
also attach cookies automatically, so another site can trigger an
authenticated state change unless the application binds that request to the
user's session and origin.

## Contract

- Use an auto-escaping template or context-specific encoder for every
  untrusted value. Never build HTML with `format!`.
- Parameterize SQL; escaping HTML is not SQL-injection defense.
- Protect cookie-authenticated state changes with an unpredictable,
  session-bound CSRF token and appropriate `SameSite` cookie policy.
- Validate `Origin`/`Referer` as defense in depth where the deployment can do
  so reliably.
- Keep state-changing operations off GET.
- Allow redirects only to a fixed route or a validated same-origin target.
- Authenticate client-carried state with a maintained AEAD or MAC library.
  A MAC provides integrity, not confidentiality; rotate keys and set expiry.
- Store one-time/ephemeral messages server-side or in short-lived,
  authenticated state without sensitive details.

## Bad

```rust
pub fn page(name: &str) -> String {
    format!("<p>Welcome {name}</p>")
}
```

## Good

```text
render(template, untrusted_value) -> auto-escaped HTML
csrf.verify_constant_time(session_token, submitted_token)
redirect(allowlisted_same_origin_path)
```

## Failure Tests

- HTML/script payloads render as text, not markup;
- missing, wrong-session, replayed, and expired CSRF tokens are rejected;
- cross-origin state-changing requests fail;
- external redirect targets fail;
- modified or expired authenticated state fails without revealing keys.

## See Also

- [api-session-security](api-session-security.md) - secure cookie and session policy
- [api-authz-fail-closed](api-authz-fail-closed.md) - authorization still applies after CSRF validation
- [api-extract-or-reject](api-extract-or-reject.md) - parse boundary data before effects
- [obs-no-sensitive-data](obs-no-sensitive-data.md) - keep tokens and user input out of telemetry
- [test-http-blackbox](test-http-blackbox.md) - test browser-facing headers and responses
