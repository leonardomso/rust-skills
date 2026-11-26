# proj-workspace-deps

> Use workspace dependency inheritance for consistent versions across crates

## Why It Matters

Multi-crate workspaces often have dependency version drift—different crates using different versions of the same dependency. Workspace dependency inheritance (Rust 1.64+) lets you declare dependencies once in the workspace `Cargo.toml` and inherit them in member crates, ensuring consistency.

## Bad

```toml
# crate-a/Cargo.toml
[dependencies]
serde = "1.0.150"
tokio = "1.25"

# crate-b/Cargo.toml
[dependencies]
serde = "1.0.188"  # Different version!
tokio = "1.32"     # Different version!

# Version drift leads to:
# - Larger binaries (multiple versions)
# - Compilation time increase
# - Subtle behavior differences
```

## Good

```toml
# Root Cargo.toml
[workspace]
members = ["crate-a", "crate-b", "crates/core"]
resolver = "3"  # default for the 2024 edition; use "2" for 2021

[workspace.dependencies]
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1.32", features = ["rt-multi-thread"] }
thiserror = "2"
criterion = "0.8"                       # dev- and build-dependencies work too
my-core = { path = "crates/core", version = "0.1" }  # internal crates too

# crate-a/Cargo.toml
[dependencies]
serde.workspace = true
tokio = { workspace = true, features = ["net"] }  # workspace features plus local ones
my-core.workspace = true

[dev-dependencies]
criterion.workspace = true

# crate-b/Cargo.toml
[dependencies]
serde.workspace = true
thiserror.workspace = true
```

The same sharing works for package metadata with `[workspace.package]` (`version.workspace = true`, `edition.workspace = true`, `license.workspace = true`).

## Optional Dependencies

`optional` is not allowed in `[workspace.dependencies]`. Set it in the member:

```toml
# Root Cargo.toml
[workspace.dependencies]
serde = "1.0"

# crate-a/Cargo.toml
[dependencies]
serde = { workspace = true, optional = true }

[features]
serde = ["dep:serde"]
```

## Turning Off Inherited Default Features

Since Rust 1.99, a member on edition 2024 or later can override an inherited dependency's `default-features`:

```toml
# crate-a/Cargo.toml (edition = "2024")
[dependencies]
serde = { workspace = true, default-features = false }  # honored on edition 2024+
```

On earlier editions, `default-features = false` next to `workspace = true` is ignored with a warning.

## Finding Unused Entries

Cargo's `unused_workspace_dependencies` lint (warn by default since Rust 1.100) reports `[workspace.dependencies]` entries that no member uses. See [lint-cargo-lints](lint-cargo-lints.md).

## See Also

- [proj-lib-main-split](./proj-lib-main-split.md) - Workspace structure
- [api-serde-optional](./api-serde-optional.md) - Optional dependencies
- [lint-workspace-lints](./lint-workspace-lints.md) - Workspace lints
- [lint-cargo-lints](./lint-cargo-lints.md) - Find unused dependencies
- [proj-dependency-cooldown](./proj-dependency-cooldown.md) - Delay brand-new versions
- [macro-pin-impl-crate](macro-pin-impl-crate.md) - Pin companion proc-macro crates
