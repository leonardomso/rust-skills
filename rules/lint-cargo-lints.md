# lint-cargo-lints

> Configure Cargo's own lints in `[lints.cargo]` and deny unused dependencies

## Why It Matters

Since Rust 1.100, Cargo emits some of its warnings as lints that you control in a `[lints.cargo]` table, the same way you control `[lints.rust]` and `[lints.clippy]`. The new `cargo::unused_dependencies` lint finds dependencies that are declared but never used, a check that previously needed an external tool such as `cargo-udeps` or `cargo-machete`. Unused dependencies slow builds and widen your supply-chain surface.

## Bad

```toml
[package]
name = "my-app"
version = "0.1.0"
edition = "2024"

[dependencies]
serde = "1"
itoa = "1"   # nothing in src/ uses this, and no one notices
```

## Good

```toml
[package]
name = "my-app"
version = "0.1.0"
edition = "2024"

[dependencies]
serde = "1"

[lints.cargo]
unused_dependencies = "deny"
```

Running `cargo check` now fails with:

```text
error: unused dependency `itoa`
  = note: `cargo::unused_dependencies` is set to `deny` in `[lints]`
help: consider removing the dependency on `itoa`
```

## Workspaces

```toml
# Root Cargo.toml
[workspace.lints.cargo]
unused_dependencies = "deny"
unused_workspace_dependencies = "warn"
unused_workspace_package_fields = "warn"

# member/Cargo.toml
[lints]
workspace = true
```

The key is the lint name without the `cargo::` prefix. Lints can also be grouped (`cargo::correctness`, `cargo::style`, `cargo::suspicious`, `cargo::pedantic`, `cargo::restriction`) and given a `priority`, like clippy groups.

## Useful Lints

| Lint | Default | What it reports |
|------|---------|-----------------|
| `unused_dependencies` | warn | Dependency declared but never used |
| `unused_workspace_dependencies` | warn | `[workspace.dependencies]` entry no member uses |
| `unused_workspace_package_fields` | warn | `[workspace.package]` field no member inherits |
| `missing_lints_inheritance` | warn | `[workspace.lints]` exists but a member has no `[lints]` |
| `blanket_hint_mostly_unused` | warn | `hint-mostly-unused` applied to every dependency |
| `non_kebab_case_bins` / `_features` / `_packages` | allow | Naming convention checks |

## Notes

- `unused_dependencies` only checks `[dependencies]` and `[build-dependencies]` of the selected packages. `[dev-dependencies]` are not checked, and `cargo check --bin foo` skips `[dependencies]` entirely, so run a plain `cargo check` (or `--workspace`) in CI.
- A dependency added only to activate a feature of a transitive dependency is reported as a false positive. Move it under `[target.'cfg(false)'.dependencies]`.
- These lints are separate from `clippy::cargo`, which checks manifest metadata. See [lint-cargo-metadata](lint-cargo-metadata.md).

## See Also

- [lint-workspace-lints](lint-workspace-lints.md) - share lint levels across a workspace
- [proj-workspace-deps](proj-workspace-deps.md) - workspace dependency inheritance
- [lint-cargo-metadata](lint-cargo-metadata.md) - clippy's manifest metadata lints
- [lint-build-warnings](lint-build-warnings.md) - fail CI on warnings
