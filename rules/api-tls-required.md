# api-tls-required

> Require authenticated TLS for production network hops and never silently downgrade certificate validation

## Why It Matters

Passwords, session cookies, database credentials, and API tokens are bearer
secrets. Encoding does not protect them. Encryption without peer
authentication still permits interception. Production clients and servers
must use TLS with hostname and certificate validation, and internal networks
are not an exemption.

## Contract

- Terminate TLS at a documented trusted boundary and protect every hop beyond
  it with TLS or authenticated workload transport.
- Verify certificate chain, hostname, validity, and intended trust roots.
- Never ship an "accept invalid certificates" or plaintext fallback in the
  production configuration.
- Require TLS for database, cache, queue, and outbound HTTP connections that
  cross a process boundary.
- Keep private keys and trust material in a secret/certificate manager with
  rotation.
- Set connect and handshake deadlines and expose failures through readiness or
  dependency telemetry without logging credentials.
- Test the real production TLS mode, including wrong hostname, expired or
  untrusted certificate, and rotation overlap.

## Bad

```rust
pub struct TlsPolicy {
    pub accept_invalid_certificates: bool,
    pub plaintext_fallback: bool,
}
```

## Good

```rust
pub enum TransportPolicy {
    AuthenticatedTls,
    LocalTestOnlyPlaintext,
}

pub fn production_policy() -> TransportPolicy {
    TransportPolicy::AuthenticatedTls
}

fn main() {
    assert!(matches!(
        production_policy(),
        TransportPolicy::AuthenticatedTls
    ));
}
```

## Failure Tests

- an untrusted issuer is rejected;
- a valid certificate for the wrong hostname is rejected;
- expired and not-yet-valid certificates are rejected;
- production configuration refuses plaintext and disabled validation;
- certificate rotation succeeds while old and new trust overlap;
- handshake timeout removes readiness without causing a restart loop.

## See Also

- [proj-typed-config](proj-typed-config.md) - make transport policy explicit and typed
- [async-http-client-reuse](async-http-client-reuse.md) - configure outbound policy once
- [api-password-auth](api-password-auth.md) - credentials require confidential transport
- [api-session-security](api-session-security.md) - cookies require `Secure`
- [obs-no-sensitive-data](obs-no-sensitive-data.md) - report TLS failure without secrets
