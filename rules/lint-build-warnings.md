# lint-build-warnings

> Deny warnings in CI with `build.warnings` instead of `RUSTFLAGS=-Dwarnings`

## Why It Matters

`RUSTFLAGS="-D warnings"` changes the compiler flags for every crate, including dependencies, build scripts and proc macros. A new warning in a dependency, or a newer toolchain adding a lint, then breaks your build for reasons you cannot fix. It also invalidates caches shared with builds that use different flags. Cargo's `build.warnings` setting (stable since Rust 1.97) applies only to lint warnings from your own workspace packages.

## Bad

```bash
# Changes the flags for all crates and fails on warnings from anywhere
RUSTFLAGS="-D warnings" cargo build
cargo clippy -- -D warnings
```

## Good

```toml
# .cargo/config.toml
[build]
warnings = "deny"
```

```bash
# Or only in CI, with an environment variable
CARGO_BUILD_WARNINGS=deny cargo clippy --workspace --all-targets
CARGO_BUILD_WARNINGS=deny cargo doc --workspace --no-deps
```

The levels are `"warn"` (default), `"allow"` and `"deny"`. With `deny`, a crate that has lint warnings fails with `warnings are denied by build.warnings configuration`. Add `--keep-going` to see the warnings of all crates in one run.

## Notes

- Only warnings that are lints are affected. Other warnings, and warnings from dependencies, are left as they are.
- Do not put `warnings = "deny"` in a committed `.cargo/config.toml` that local developers also use if you want them to experiment freely. Prefer the environment variable in the CI workflow.
- For finer control, deny specific lints in `[workspace.lints]`. See [lint-workspace-lints](lint-workspace-lints.md).

## See Also

- [lint-workspace-lints](lint-workspace-lints.md) - lint levels in Cargo.toml
- [lint-deny-correctness](lint-deny-correctness.md) - correctness lints and CI
- [lint-cargo-lints](lint-cargo-lints.md) - Cargo's own lints
