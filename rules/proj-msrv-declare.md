# proj-msrv-declare

> Declare `rust-version` (MSRV) in Cargo.toml and test it in CI

## Why It Matters

Setting `package.rust-version` causes Cargo to emit a clear, actionable error when the installed toolchain is too old, instead of a cryptic type or feature error deep inside your code. The 2024-edition resolver (resolver = "3", the default for edition 2024) is MSRV-aware: it will avoid selecting dependency versions whose own `rust-version` field exceeds yours, preventing accidental MSRV breakage from transitive upgrades. Without a declared MSRV, you have no contract with downstream users and no CI gate to catch regressions.

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
rust-version = "1.85"  # edition 2024 floor; raise when the code requires it

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
  run: cargo check --all-features
```

## Choosing and Maintaining MSRV

- Declare the MSRV when a library is created; retrofitting the promise after users depend on the crate is harder.
- Keep `rust-version` at or above the selected edition's minimum compiler
  release (Rust 1.85 for edition 2024).
- Keep it a few stable releases behind current Rust by default. Choose a wider lag only for measured user constraints such as embedded targets or a documented corporate freeze.
- Do not chase the oldest toolchain that can compile by accident—a very low floor widens eligible dependency versions and can force users onto older, buggier releases.
- When you bump MSRV, treat it as a semver-minor change (for libraries) and document it in your changelog.
- A major version does not improve MSRV compatibility: downstream projects already resolve every dependency's toolchain floor, and an unnecessary major can split the graph into two versions.
- Run `cargo msrv` (the `cargo-msrv` tool) to find the actual floor automatically.

## See Also

- [proj-workspace-deps](proj-workspace-deps.md) - use workspace dependency inheritance
- [lint-cargo-metadata](lint-cargo-metadata.md) - warn on missing Cargo.toml metadata
- [doc-cargo-metadata](doc-cargo-metadata.md) - fill Cargo.toml metadata fields
