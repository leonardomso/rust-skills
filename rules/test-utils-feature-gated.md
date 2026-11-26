# test-utils-feature-gated

> Put mocks, fake data, and safety-check overrides behind a `test-util` feature

## Why It Matters

Helpers that bypass checks, expose secrets, or fake I/O are useful in tests and dangerous in production. If they are always compiled in, any caller can reach them, and one stray call can disable certificate validation or leak a token. Gating them behind one clearly named feature keeps them out of release builds by default, and downstream crates can still opt in from their `dev-dependencies`.

## Bad

```rust
pub struct HttpClient {
    verify_certs: bool,
}

impl HttpClient {
    // Always compiled in; production code can disable verification
    pub fn bypass_certificate_checks(&mut self) {
        self.verify_certs = false;
    }
}
```

## Good

```toml
# Cargo.toml
[features]
test-util = []
```

```rust
pub struct HttpClient {
    verify_certs: bool,
}

impl HttpClient {
    pub fn new() -> Self {
        Self { verify_certs: true }
    }

    // Only available to tests in this crate or to crates that enable test-util
    #[cfg(any(test, feature = "test-util"))]
    pub fn bypass_certificate_checks(&mut self) {
        self.verify_certs = false;
    }

    pub fn verifies_certs(&self) -> bool {
        self.verify_certs
    }
}
```

Downstream crates enable it only for their own tests:

```toml
[dev-dependencies]
my-http = { version = "1", features = ["test-util"] }
```

## Notes

- Use one feature named `test-util`, not one per helper.
- The feature must be additive: enabling it adds items, it never changes the behavior of existing ones.

## See Also

- [proj-feature-additive](proj-feature-additive.md) - Features must only add functionality
- [test-mock-traits](test-mock-traits.md) - Mock through traits
- [test-integration-dir](test-integration-dir.md) - Integration tests use the public API
- [lint-cfg-check](lint-cfg-check.md) - Catch typos in feature names
- Source: Microsoft Pragmatic Rust Guidelines, M-TEST-UTIL
