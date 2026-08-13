# ffi-sys-crate-builds

> Keep `-sys` crates hermetic: build verifiable vendored sources with Rust tooling and offer static or dynamic loading

## Why It Matters

Every consumer of `foo-sys` inherits its build. A `build.rs` that shells out to `nasm`, `perl`, `pkg-config`, or a downloaded tarball fails on the next machine, in CI, and in any sandbox that has only `cc` and a linker. Keep a `-sys` crate hermetic: vendor upstream sources with their repository URL and exact revision, generate bindgen output before publish when possible, and offer static linking plus a `libloading` path when runtime discovery is part of the product.

## Bad

```rust
// build.rs
fn main() {
    std::process::Command::new("perl")
        .arg("generate-bindings.pl")
        .status()
        .expect("perl must be on PATH");
}
```

## Good

```toml
# foo-sys/Cargo.toml
[package]
name = "foo-sys"
edition = "2024"

[build-dependencies]
cc = "1"
```

```text
// foo-sys/build.rs
// Compile vendored C with the `cc` crate. No perl, nasm, or network fetch
// on the default path. Sources live in vendor/ next to this script.
//
//   println!("cargo::rerun-if-changed=vendor/foo.c");
//   cc::Build::new().file("vendor/foo.c").include("vendor").compile("foo");
//
// vendor/UPSTREAM records:
//   repository = "https://example.invalid/foo"
//   revision = "<full source commit>"
```

```rust
pub fn linked_native_lib() -> &'static str {
    "foo"
}

fn main() {
    let _ = linked_native_lib();
}
```

An already-hermetic Rust crate that wraps an upstream native build system may
be used instead of reproducing every command in `cc`. Likewise, a hermetic
build service may provide a source root through a documented environment
variable; validate the path and hash, and never make an ambient workstation
variable the only build route.

## See Also

- [ffi-sys-vs-ffi-name](ffi-sys-vs-ffi-name.md) - this contract applies to `*-sys`, not to `*-ffi` export crates
- [proj-build-rs-minimal](proj-build-rs-minimal.md) - keep the script deterministic and offline
- [proj-works-out-of-box](proj-works-out-of-box.md) - the same "just `cargo build`" bar for ordinary libraries
