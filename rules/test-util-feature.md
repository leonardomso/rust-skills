# test-util-feature

> Put safe testing utilities behind an additive feature; never use a feature to weaken a production invariant

## Why It Matters

Cargo features are capabilities, not build profiles. Dependency feature
unification means a `test-util` feature enabled anywhere in a resolved graph may
also be present in a release build. It is useful for deterministic clocks,
scripted transports, and observable test controllers only when those APIs
remain safe if accidentally enabled. Certificate bypasses, authorization
shortcuts, secret extractors, and other invariant-breaking controls do not
become safe merely because their symbols are feature-gated.

## Bad

```rust
pub struct TlsClient {
    verify_peer: bool,
}

impl TlsClient {
    #[cfg(feature = "test-util")]
    pub fn skip_hostname_check(&mut self) {
        // A downstream release can enable this feature through unification.
        self.verify_peer = false;
    }
}
```

## Good

```rust
pub trait Clock {
    fn now_millis(&self) -> u64;
}

pub struct SystemClock;

impl Clock for SystemClock {
    fn now_millis(&self) -> u64 {
        0 // Call the platform clock in the real adapter.
    }
}

#[cfg(feature = "test-util")]
#[derive(Clone)]
pub struct ManualClock {
    now_millis: u64,
}

#[cfg(feature = "test-util")]
impl ManualClock {
    pub fn new(now_millis: u64) -> Self {
        Self { now_millis }
    }
}

#[cfg(feature = "test-util")]
impl Clock for ManualClock {
    fn now_millis(&self) -> u64 {
        self.now_millis
    }
}

fn main() {
    let _ = SystemClock;
}
```

Enabling `ManualClock` in a release artifact adds a deterministic adapter but
does not disable authentication, validation, or transport security.

## Key Points

- Assume every published feature can be enabled in production.
- Keep features additive: they may add safe fakes or controllers, but must not
  remove checks or change secure defaults.
- Keep crate-internal helpers under `#[cfg(test)]` when integration consumers do
  not need them.
- Put destructive fault injectors and invariant bypasses in a separate test
  harness or test-only crate that is absent from the production dependency
  graph.
- Test default and all-feature builds. Inspect resolved features when a release
  unexpectedly contains test support.
- Name the feature consistently (`test-util` is conventional) and declare it to
  `check-cfg` so misspellings fail loudly.

## See Also

- [test-mock-traits](test-mock-traits.md) - inject deterministic effects without weakening invariants
- [proj-feature-additive](proj-feature-additive.md) - dependency features unify and must compose safely
- [lint-cfg-check](lint-cfg-check.md) - validate feature names
- [api-tls-required](api-tls-required.md) - certificate validation has no feature-gated bypass
