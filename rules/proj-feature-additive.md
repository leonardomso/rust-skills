# proj-feature-additive

> Design Cargo features to be strictly additive

## Why It Matters

Features should add capability or dependency support without removing the
baseline contract. Even an added trait implementation can create coherence or
method-resolution conflicts, so it needs ordinary API compatibility review.
Mutually exclusive backend features do not compose under unification; model
runtime/provider choice as data or separate facade crates instead.

## Bad

```toml
[features]
# "no_std" disables std — enabling it REMOVES behavior
no_std = []

[dependencies]
# and somewhere in lib.rs:
# #[cfg(not(feature = "no_std"))]
# use std::collections::HashMap;
```

```rust
// lib.rs — toggling off std via a feature is non-additive
#[cfg(not(feature = "no_std"))]
use std::vec::Vec;

#[cfg(feature = "no_std")]
use alloc::vec::Vec;
```

## Good

```toml
[features]
# "std" ADDS std support; no_std is the baseline
default = ["std"]
std = []

# Optional integrations — purely additive
serde = ["dep:serde"]
tokio = ["std", "dep:tokio"]

[dependencies]
serde = { version = "1", optional = true, default-features = false, features = ["alloc", "derive"] }
tokio = { version = "1", optional = true, default-features = false, features = ["rt"] }
```

```rust
// lib.rs — std is opt-in, no_std is the default baseline
// Crate-root attribute:
// #![cfg_attr(not(feature = "std"), no_std)]

#[cfg(not(feature = "std"))]
extern crate alloc;

#[cfg(not(feature = "std"))]
use alloc::vec::Vec;
#[cfg(feature = "std")]
use std::vec::Vec;
```

## Rules for Additive Features

- A feature may add items, dependencies, or integrations, but every added
  public impl or variant still needs coherence and semver review.
- If you ship a `no_std` crate, make `std` a feature in `default`, not the other way around.
- Every feature must work in every unified combination. Do not publish mutually exclusive features, and do not use `compile_error!` as the normal backend-selection mechanism.
- Test `--no-default-features`, each feature individually, `--all-features`,
  and supported pairwise/high-risk combinations on every applicable target.
- A feature enables every feature it requires; callers must not need to discover and add a second feature manually.
- Do not rely on a parent crate suppressing a child dependency feature. Another graph path may enable it, and Cargo will unify it globally.
- Use `dep:` syntax (`dep:serde`) to keep optional dependency names out of the feature namespace.
- Name the capability (`serde`, `tls`, `metrics`), not a placeholder such as `extras`, `misc`, `full2`, or `unstable-stuff`.

## See Also

- [api-serde-optional](api-serde-optional.md) - gate Serialize/Deserialize behind a feature flag
- [proj-workspace-deps](proj-workspace-deps.md) - use workspace dependency inheritance
- [lint-cfg-check](lint-cfg-check.md) - catch feature-gate typos with unexpected_cfgs
- [proj-works-out-of-box](proj-works-out-of-box.md) - default features must still cargo-build everywhere
- [test-util-feature](test-util-feature.md) - test-only helpers are an additive feature
