# lint-workspace-lints

> Configure lints at workspace level for consistent enforcement

## Why It Matters

Without centralized lint configuration, each crate develops its own standards (or none). Workspace-level lints (Rust 1.74+) ensure consistent code quality across all crates. Denied lints catch issues in CI before they reach production.

## Bad

```toml
# crate-a/Cargo.toml - strict
[lints.clippy]
unwrap_used = "deny"

# crate-b/Cargo.toml - lenient
# No lint config

# crate-c/Cargo.toml - different
[lints.clippy]
unwrap_used = "warn"

# Inconsistent enforcement, some issues slip through
```

## Good

```toml
# Root Cargo.toml
[workspace.lints.rust]
unsafe_code = "deny"
missing_docs = "warn"

[workspace.lints.clippy]
# Correctness
unwrap_used = "deny"
expect_used = "warn"
panic = "deny"

# Style
needless_pass_by_value = "warn"
redundant_clone = "warn"

[workspace.lints.cargo]
unused_dependencies = "deny"

[workspace.lints.rustdoc]
broken_intra_doc_links = "deny"

# crate-a/Cargo.toml
[lints]
workspace = true

# crate-b/Cargo.toml
[lints]
workspace = true
```

## Recommended Lint Configuration

```toml
# Root Cargo.toml
[workspace.lints.rust]
# Safety
unsafe_code = "deny"
missing_debug_implementations = "warn"

# Quality
unused_results = "warn"
unused_qualifications = "warn"

[workspace.lints.clippy]
# === Correctness (deny) ===
correctness = { level = "deny", priority = -1 }

# === Suspicious (deny) ===
suspicious = { level = "deny", priority = -1 }

# === Style (warn) ===
style = { level = "warn", priority = -1 }

# === Complexity (warn) ===
complexity = { level = "warn", priority = -1 }

# === Perf (warn) ===
perf = { level = "warn", priority = -1 }

# === Pedantic (selective) ===
# Not all pedantic lints are useful
doc_markdown = "warn"
needless_pass_by_value = "warn"
redundant_closure_for_method_calls = "warn"
semicolon_if_nothing_returned = "warn"

# === Nursery (selective) ===
useless_let_if_seq = "warn"

# === Restriction (selective) ===
cognitive_complexity = "warn"
unwrap_used = "deny"
expect_used = "warn"
dbg_macro = "warn"
print_stdout = "warn"  # Use logging instead
todo = "warn"

[workspace.lints.cargo]
# Cargo's own lints (stable since Rust 1.100), see lint-cargo-lints
unused_dependencies = "warn"
unused_workspace_dependencies = "warn"

[workspace.lints.rustdoc]
broken_intra_doc_links = "deny"
private_intra_doc_links = "warn"
```

A `[workspace.lints]` table is not inherited automatically. Every member needs `[lints] workspace = true` (or an explicit empty `[lints]` table). The `cargo::missing_lints_inheritance` lint (warn by default since Rust 1.100) flags members that forget.

## Per-Crate Overrides

```toml
# crate-with-binary/Cargo.toml
[lints]
workspace = true

# Binary entry point can use unwrap
[lints.clippy]
unwrap_used = "allow"

# test-utils/Cargo.toml
[lints]
workspace = true

# Test utilities can print
[lints.clippy]
print_stdout = "allow"
```

## CI Integration

```yaml
# .github/workflows/ci.yml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: clippy
      
      - name: Clippy
        run: cargo clippy --workspace --all-targets
        env:
          CARGO_BUILD_WARNINGS: deny

      - name: Rustdoc
        run: cargo doc --workspace --no-deps
        env:
          CARGO_BUILD_WARNINGS: deny
```

`build.warnings = "deny"` (stable since Rust 1.97) fails the build on lint warnings from your own packages only. Unlike `-D warnings` in `RUSTFLAGS`, it does not touch the compiler flags and it ignores warnings from dependencies. See [lint-build-warnings](lint-build-warnings.md).

## Lint Categories

```toml
# Category-level configuration
[workspace.lints.clippy]
# All lints in category at once
correctness = { level = "deny", priority = -1 }
suspicious = { level = "deny", priority = -1 }
style = { level = "warn", priority = -1 }
complexity = { level = "warn", priority = -1 }
perf = { level = "warn", priority = -1 }
pedantic = { level = "warn", priority = -1 }

# Then override specific lints (higher priority)
missing_errors_doc = "allow"  # Override pedantic
```

## See Also

- [lint-clippy-groups](./lint-clippy-groups.md) - Critical lints
- [proj-workspace-deps](./proj-workspace-deps.md) - Workspace configuration
- [lint-cargo-lints](./lint-cargo-lints.md) - `[lints.cargo]` table
- [lint-build-warnings](./lint-build-warnings.md) - deny warnings in CI with `build.warnings`
- [err-no-unwrap-prod](./err-no-unwrap-prod.md) - unwrap lints
- [lint-expect-over-allow](lint-expect-over-allow.md) - Prefer #[expect] over #[allow]
