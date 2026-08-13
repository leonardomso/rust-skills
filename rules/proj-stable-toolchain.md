# proj-stable-toolchain

> Build and run production applications on a pinned stable toolchain and test upgrades continuously

## Why It Matters

`stable`, `beta`, and `nightly` are release channels, while a target triple
selects the platform. Floating implicitly with the developer machine makes CI
and production disagree; shipping nightly ties the product to unfinished
features. Pin the current stable release used for admission and upgrade it
deliberately.

## Contract

- Install and select toolchains with `rustup` or an equivalent hermetic
  mechanism.
- Commit `rust-toolchain.toml` with an exact stable version and required
  components/targets.
- Build, test, and run the shipped application on stable.
- Use nightly only for explicitly isolated tools such as Miri or fuzzing; do
  not make the production binary depend on nightly features.
- Test the next stable/beta channel as advisory early warning while the pinned
  stable toolchain remains admission authority.
- Honor Rust target-tier guarantees and test every advertised deployment
  target.
- Upgrade regularly with the dependency graph and review compiler/lint changes
  rather than postponing them indefinitely.

## Good

```toml
[toolchain]
channel = "1.97.0"
profile = "minimal"
components = ["clippy", "rustfmt"]
targets = ["x86_64-unknown-linux-gnu"]
```

## See Also

- [proj-msrv-declare](proj-msrv-declare.md) - library compatibility policy is separate from the app toolchain
- [proj-latest-edition](proj-latest-edition.md) - edition is not a release channel
- [proj-works-out-of-box](proj-works-out-of-box.md) - keep target builds free of hidden host tools
- [lint-rustfmt-check](lint-rustfmt-check.md) - pin formatter behavior with the toolchain
- [unsafe-miri-ci](unsafe-miri-ci.md) - isolate nightly-only verification
