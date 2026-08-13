# lint-warnings-deny-config

> Prefer Cargo `[build] warnings = "deny"` over `RUSTFLAGS=-Dwarnings` for rustc CI

## Why It Matters

`RUSTFLAGS=-Dwarnings` treats rustc warnings as errors, but it also changes the compiler flag set for every crate Cargo builds. That busts the incremental and shared rustc cache, so CI and local `cargo test` rebuild more than they should. Cargo 1.97 stabilized `build.warnings`, which applies the same rustc-warning policy to local packages without rewriting `RUSTFLAGS`. Keep Clippy's `-D warnings` — `build.warnings` does not control Clippy.

## Bad

```bash
# Applies to every rustc invocation and invalidates cached artifacts
export RUSTFLAGS="-Dwarnings"
cargo test --workspace
```

```yaml
# .github/workflows/ci.yml
- name: Build
  env:
    RUSTFLAGS: "-Dwarnings"
  run: cargo test --workspace
```

## Good

```toml
# .cargo/config.toml — Cargo 1.97+
[build]
warnings = "deny"
```

```yaml
# .github/workflows/ci.yml
- name: Build
  run: cargo test --workspace

- name: Clippy
  run: cargo clippy --workspace --all-targets -- -D warnings
```

## Notes

- `build.warnings` accepts `"warn"` (default), `"deny"`, and `"allow"`. Use `"deny"` in CI so new rustc warnings fail the build.
- The setting is documented in the Cargo Book as `build.warnings`. It covers rustc lints from your packages; it is not a substitute for `cargo clippy -- -D warnings`.
- Prefer a checked-in `.cargo/config.toml` (or a CI `--config 'build.warnings="deny"'` override) over a global `RUSTFLAGS` export.

## See Also

- [lint-workspace-lints](lint-workspace-lints.md) - configure rustc and Clippy lints in Cargo.toml
- [lint-deny-correctness](lint-deny-correctness.md) - deny Clippy correctness lints
- [lint-cfg-check](lint-cfg-check.md) - catch cfg typos before they become silent dead code
