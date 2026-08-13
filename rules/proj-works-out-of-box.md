# proj-works-out-of-box

> Default features must `cargo build` on tier-1 targets with only the Rust toolchain — no extra packages, env vars, or generated-at-install steps

## Why It Matters

An application with two hundred crates will not survive a leaf that needs `protoc`, `openssl-src` plus Perl, or `SOME_SDK_ROOT` on every laptop. "it compiled on my machine" is a defect: if the crate is not *about* a platform, its default feature set builds on every tier-1 target with `cargo` and `cc`. Generate bindings and data files before you publish; gate optional native extras behind additive features. CI that runs `cargo check --workspace` on linux/mac/windows is the mechanical check.

## Bad

```toml
# Cargo.toml
[package]
name = "inventory"
edition = "2024"

[dependencies]
# Always on: every consumer must have the native SDK installed.
device-sdk-sys = "1"
```

```rust
fn main() {
    // build.rs equivalent: refuse to compile unless an SDK path is exported
    let _ = std::env::var("DEVICE_SDK_ROOT").expect("set DEVICE_SDK_ROOT");
}
```

If support for a tier-1 target is temporarily incomplete, keep the platform
edge behind an internal HAL and provide a dummy implementation that compiles
and returns an explicit unsupported error. That preserves an extension point
without pretending the hardware works. Use `cfg(target_os = ...)` for genuine
platform selection and additive opt-in features for optional SDK capability.

## Good

```toml
# Cargo.toml
[package]
name = "inventory"
edition = "2024"

[features]
default = []
hardware = ["dep:device-sdk-sys"]

[dependencies]
device-sdk-sys = { version = "1", optional = true }
```

```rust
pub fn sku_count(rows: &[(u32, u32)]) -> u32 {
    rows.iter().map(|(_, n)| n).sum()
}

fn main() {
    assert_eq!(sku_count(&[(1, 2), (2, 3)]), 5);
}
```

## See Also

- [proj-feature-additive](proj-feature-additive.md) - optional native bits add items; they never remove the default build
- [ffi-sys-crate-builds](ffi-sys-crate-builds.md) - when you *are* the `-sys` crate, vendor or probe instead of requiring host tools
- [proj-build-rs-minimal](proj-build-rs-minimal.md) - no network and no surprise env vars in `build.rs`
