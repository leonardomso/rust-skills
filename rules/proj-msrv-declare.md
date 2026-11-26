# proj-msrv-declare

> Declare `rust-version` (MSRV) in Cargo.toml and test it in CI

## Why It Matters

Setting `package.rust-version` causes Cargo to emit a clear, actionable error when the installed toolchain is too old, instead of a cryptic type or feature error deep inside your code. The resolver is MSRV-aware by default with `resolver = "3"` (the default for edition 2024): it avoids dependency versions whose own `rust-version` exceeds yours, preventing accidental MSRV breakage from transitive upgrades. Edition 2024 itself needs Rust 1.85, so that is the lowest MSRV for a 2024 crate. Without a declared MSRV, you have no contract with downstream users and no CI gate to catch regressions.

## Bad

```toml
[package]
name = "my-crate"
version = "0.1.0"
edition = "2021"
# no rust-version — users get cryptic errors on old toolchains,
# and nothing prevents a dep bump from silently raising the floor
```

## Good

```toml
[package]
name = "my-crate"
version = "0.1.0"
edition = "2024"
rust-version = "1.85"  # oldest toolchain you commit to supporting (edition 2024 needs 1.85)

[workspace]
resolver = "3"  # default for edition 2024; enables MSRV-aware dep resolution
```

CI job pinning the MSRV toolchain (GitHub Actions example):

```yaml
# .github/workflows/msrv.yml
- name: Install MSRV toolchain
  uses: dtolnay/rust-toolchain@master
  with:
    toolchain: "1.85"

- name: Check MSRV
  run: cargo check --all-features --locked
```

## MSRV-Aware Resolution

With resolver 3, `cargo add` and `cargo update` pick the newest dependency versions that fit your `rust-version`. The behaviour is controlled by `resolver.incompatible-rust-versions` in `.cargo/config.toml`:

```toml
# .cargo/config.toml
[resolver]
incompatible-rust-versions = "fallback"  # prefer compatible versions, allow others if none fit
```

Use `"allow"` to ignore `rust-version` while resolving. A one-off `cargo update --ignore-rust-version` or `cargo update --precise` overrides the check. Declaring `rust-version` also lets clippy's `incompatible_msrv` lint (in `clippy::suspicious`) flag std APIs newer than your MSRV.

## Choosing and Maintaining MSRV

- Pick the oldest stable toolchain your users are realistically running (check distro packages, embedded targets, corporate freeze windows).
- Do not go lower than needed — a lower MSRV widens the set of eligible dependency versions and can force you onto older, buggier releases.
- When you bump MSRV, treat it as a semver-minor change (for libraries) and document it in your changelog.
- Run `cargo msrv` (the `cargo-msrv` tool) to find the actual floor automatically.

## See Also

- [proj-workspace-deps](proj-workspace-deps.md) - use workspace dependency inheritance
- [proj-dependency-cooldown](proj-dependency-cooldown.md) - delay adopting freshly published dependency versions
- [lint-cargo-metadata](lint-cargo-metadata.md) - warn on missing Cargo.toml metadata
- [doc-cargo-metadata](doc-cargo-metadata.md) - fill Cargo.toml metadata fields
