# proj-dependency-cooldown

> Set a minimum publish age so the resolver skips brand-new dependency versions

## Why It Matters

Malicious or broken releases are usually yanked within hours or days. A dependency cooldown makes the resolver ignore versions published more recently than a chosen age, so `cargo update` and `cargo add` do not pull in a release the moment it appears. Cargo supports this since Rust 1.100 (RFC 3923). Versions already in `Cargo.lock` are not affected.

## Bad

```bash
# Pulls whatever was published a minute ago
cargo update
```

## Good

```toml
# .cargo/config.toml
[registry]
global-min-publish-age = "7 days"   # all registries

[resolver]
incompatible-publish-age = "deny"   # default: ignore too-new versions
```

With this config, `cargo update` reports that it locked packages "as of 7 days ago" and skips newer versions. Accepted units are seconds, minutes, hours, days, weeks and months. `"0"` allows everything.

Per-registry values override the global one:

```toml
[registries.my-registry]
min-publish-age = "0"   # trust the internal registry immediately
```

## Taking a Fix Immediately

When a security fix was published today, bypass the cooldown for that one update:

```bash
# one-off: allow new versions
cargo update --config resolver.incompatible-publish-age='"allow"' -p vulnerable-crate
# or pin a specific version
cargo update -p vulnerable-crate --precise 1.2.4
```

## Related Supply-Chain Defaults

- Commit `Cargo.lock` for binaries and use `--locked` in CI so builds use exactly what you reviewed.
- Since Rust 1.100, `cargo install` uses the lockfile packaged in the `.crate` by default, so `cargo install --locked` is now a no-op. Older toolchains still need `--locked`.
- Combine with MSRV-aware resolution. See [proj-msrv-declare](proj-msrv-declare.md).

## Notes

- The check needs the registry index to carry publish times. The setting is ignored for registries that do not support it.
- Versions already recorded in `Cargo.lock` stay selectable, so the cooldown never forces a downgrade.

## See Also

- [proj-msrv-declare](proj-msrv-declare.md) - MSRV-aware resolver
- [lint-cargo-lints](lint-cargo-lints.md) - find unused dependencies
- [proj-workspace-deps](proj-workspace-deps.md) - one place for dependency versions
