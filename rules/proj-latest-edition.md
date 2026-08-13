# proj-latest-edition

> Create new crates and workspaces on the latest stable edition (2024 today)

## Why It Matters

An edition selects edition-gated syntax and name-resolution behavior, not a
compatibility firewall or a Rust release. A package on 2018 still talks to 2024
dependencies and can use release-stabilized features such as `let ... else`
when its `rust-version` is new enough; it does not receive 2024-specific
changes such as the revised prelude and unsafe-attribute rules. Set `edition`
to the newest stable when creating a crate. Staying on 2015 or 2018 does not widen the
crate graph. It can permit an older compiler floor because every edition has a
minimum Rust release; Rust 2024 requires Rust 1.85 or newer.

## Bad

```toml
# new library — old dialect on purpose, extra resolver "for compatibility"
[package]
name = "inventory"
version = "0.1.0"
edition = "2018"
resolver = "2"
```

```rust
// Older edition selected despite having no compatibility requirement.
// Edition and rust-version are separate; this does not support older rustc.
```

## Good

```toml
[package]
name = "inventory"
version = "0.1.0"
edition = "2024"
# resolver comes from the edition (3 on 2024). Set it only to override.
rust-version = "1.85" # may be higher, but never below the edition floor
```

```rust
fn main() {
    let value = 7;
    assert_eq!(value, 7);
}
```

A binary that still lives on `edition = "2015"` can depend on this crate. The editions do not have to match.

## Key Points

- **New** packages and **new** workspaces take the current stable edition. That is **2024** now; move forward when 2027 ships.
- Edition choice does **not** control which crates you may depend on. It does
  impose a minimum compiler version (1.85 for edition 2024);
  `package.rust-version` declares the package's exact supported floor at or
  above that minimum (`proj-msrv-declare`).
- Omit `resolver` unless you must override the edition default (workspace mixed-edition oddities, or pinning resolver `"2"` on a 2024 root). 2024 already means resolver `"3"`.
- **Migrating** an existing crate (`cargo fix --edition`, fixing prelude and capture changes) is a separate project from creating one. This rule does not demand a mid-release edition bump; it demands that `cargo new` not start on 2018.

## See Also

- [proj-msrv-declare](proj-msrv-declare.md) - compiler floor is `rust-version`, independent of edition
- [proj-workspace-large](proj-workspace-large.md) - a new workspace inherits edition 2024 / resolver 3
- [proj-workspace-deps](proj-workspace-deps.md) - share that edition and metadata from the root
- [proj-works-out-of-box](proj-works-out-of-box.md) - a 2024 crate still has to `cargo build` on tier-1 targets
