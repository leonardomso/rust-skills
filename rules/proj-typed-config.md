# proj-typed-config

> Deserialize layered configuration into typed values, validate it once at startup, and keep secrets out of source

## Why It Matters

Scattered environment lookups turn spelling, units, and required values into
runtime surprises deep inside handlers. Load configuration at the process
edge, combine layers with an explicit precedence order, deserialize into one
typed model, and reject invalid combinations before opening the listener.
Secrets are supplied by the deployment environment and redacted everywhere.

## Bad

```rust
pub fn request_timeout_seconds() -> u64 {
    std::env::var("TIMEOUT")
        .unwrap_or_else(|_| "30".to_owned())
        .parse()
        .unwrap()
}
```

Every call reparses ambient state, the unit is only in the function name, and
an invalid value crashes when traffic reaches that branch.

## Good

```rust
use std::net::SocketAddr;
use std::time::Duration;

pub struct Settings {
    pub listen: SocketAddr,
    pub request_timeout: Duration,
    pub database_url: SecretString,
}

pub struct SecretString(String);

impl std::fmt::Debug for SecretString {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("[redacted]")
    }
}

pub fn validate(settings: &Settings) -> Result<(), &'static str> {
    if settings.request_timeout.is_zero() {
        return Err("request timeout must be non-zero");
    }
    Ok(())
}

fn main() {
    let settings = Settings {
        listen: "127.0.0.1:8080"
            .parse()
            .expect("default listen address is a valid socket address"),
        request_timeout: Duration::from_secs(10),
        database_url: SecretString("postgres://example".to_owned()),
    };
    assert!(validate(&settings).is_ok());
}
```

## Layering Contract

Use a documented order such as:

1. bundled non-secret defaults;
2. environment-specific file or declarative state;
3. environment variables or a secret provider;
4. explicit process overrides used by tests.

Later layers replace earlier values; they do not silently merge incompatible
units. Parse URLs, addresses, durations, sizes, and enum policies into their
semantic types. Construct connection strings in one adapter rather than
concatenating fragments throughout the application.

## Key Points

- Load and validate once before spawning workers.
- Return configuration errors with the key and expected shape, never the
  secret value.
- Do not commit production credentials or bake them into images.
- Keep compile-time database query metadata separate from runtime credentials.
- Tests build a `Settings` value directly or apply a scoped override; they do
  not mutate process-wide environment variables concurrently.

## See Also

- [api-newtype-safety](api-newtype-safety.md) - represent units and secrets with distinct types
- [api-common-traits](api-common-traits.md) - redact sensitive `Debug` output
- [obs-no-sensitive-data](obs-no-sensitive-data.md) - configuration errors must not leak credentials
- [err-context-chain](err-context-chain.md) - retain which configuration layer failed
- [test-fixture-raii](test-fixture-raii.md) - scope test overrides and external resources
