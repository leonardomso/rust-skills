# api-password-reset

> Make password change and recovery single-use, time-bounded, rate-limited security workflows

## Why It Matters

A password reset bypasses the existing password by design. Long-lived,
reusable, guessable, or logged reset tokens become alternate credentials.
Changing a password without revoking sessions leaves stolen sessions active.

## Contract

- Authenticated password change verifies the current credential and applies
  the same password policy as enrollment.
- Recovery returns the same public response for known and unknown accounts.
- Generate a high-entropy token, store only a verifier/hash, bind it to the
  account and purpose, and set a short expiry.
- Tokens are single-use. Redeeming one and updating the password happen in one
  transaction.
- Revoke other sessions and outstanding reset tokens after success.
- Rate-limit request and redemption by account and network signals; alert on
  abuse without exposing account existence.
- Deliver recovery links only through a verified channel and construct URLs
  from trusted configuration, never request headers.
- Never log raw passwords or reset tokens.

## Failure Tests

- unknown and known accounts have the same status/body;
- expired, replayed, modified, and wrong-account tokens fail;
- two concurrent redemptions produce one success;
- successful reset revokes old sessions and remaining tokens;
- email/link construction cannot be changed by a forged Host header.

## See Also

- [api-password-auth](api-password-auth.md) - hash and verify the new credential
- [api-session-security](api-session-security.md) - revoke active sessions after reset
- [conc-db-transaction-boundary](conc-db-transaction-boundary.md) - consume token and update credential atomically
- [api-tls-required](api-tls-required.md) - reset links and credential submission require TLS
- [obs-no-sensitive-data](obs-no-sensitive-data.md) - redact reset tokens and account data
