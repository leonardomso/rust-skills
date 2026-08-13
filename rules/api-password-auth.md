# api-password-auth

> Hash passwords with a maintained memory-hard scheme and make authentication failures indistinguishable

## Why It Matters

Passwords are secrets with low entropy. Fast general-purpose hashes make an
offline breach cheap to attack; returning early for unknown usernames exposes
account existence through status, message, or timing. Use a maintained
password-hashing library and current policy, store the encoded PHC string, and
run both hashing and verification off the async executor.

## Contract

- Prefer a current memory-hard password hashing scheme such as Argon2id through
  a maintained library; do not implement cryptography.
- Generate an independent random salt per password and store parameters, salt,
  and hash in a standard encoded format such as PHC.
- Never store, log, serialize, or retain the raw password beyond the operation.
- Verify in `spawn_blocking` or a dedicated bounded CPU pool with admission
  control.
- For unknown users, verify against a fixed dummy hash configured with the same
  cost. Return the same status and public message as a wrong password.
- Rate-limit and monitor attempts. MFA, recovery, and credential rotation are
  product security capabilities, not optional string checks.
- Rehash after successful authentication when the stored parameters are below
  current policy.

## Bad

```rust
pub fn authenticate(stored: &str, password: &str) -> bool {
    stored == sha256(password)
}
```

## Good

```rust
pub enum CredentialResult {
    Accepted,
    Rejected,
}

pub fn public_result(valid: bool) -> CredentialResult {
    if valid {
        CredentialResult::Accepted
    } else {
        CredentialResult::Rejected
    }
}

fn main() {
    assert!(matches!(public_result(false), CredentialResult::Rejected));
}
```

The adapter performs the real library call and always reaches the same public
mapping for unknown user and wrong password.

## Failure Tests

- different salts produce different encoded hashes for the same password;
- valid and invalid passwords map to the expected result;
- unknown user and wrong password have the same status and body;
- the blocking pool is bounded under concurrent login load;
- debug output and telemetry never contain the submitted password or hash.

## See Also

- [async-spawn-blocking](async-spawn-blocking.md) - isolate CPU-heavy verification from the executor
- [api-session-security](api-session-security.md) - rotate the session after authentication
- [api-common-traits](api-common-traits.md) - redact secret `Debug`
- [obs-no-sensitive-data](obs-no-sensitive-data.md) - keep credentials out of telemetry
- [err-edge-mapping](err-edge-mapping.md) - make invalid credentials externally indistinguishable
