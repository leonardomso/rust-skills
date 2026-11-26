# api-no-glob-reexports

> Re-export items one by one, not with `pub use module::*`

## Why It Matters

A glob re-export publishes everything the module has now and everything it gains later. A new `pub` helper in the inner module silently becomes public API, and a reviewer cannot see the change in the diff. Listing the names makes the public surface deliberate and reviewable. Globs are acceptable for forwarding one platform-specific module under a `cfg`.

## Bad

```rust
mod shapes {
    pub struct Circle;
    pub struct Square;
    // Added later for internal use, now also exported by the glob below
    pub fn debug_dump() {}
}

pub use shapes::*;
```

## Good

```rust
mod shapes {
    pub struct Circle;
    pub struct Square;
    pub fn debug_dump() {}
}

// The public surface is exactly this list
#[doc(inline)]
pub use shapes::{Circle, Square};
```

## Rustdoc

Items re-exported from your own modules show up in an opaque "re-exports" block by default. Add `#[doc(inline)]` so they appear next to their siblings. Do not inline types from `std` or other crates; leaving them as plain re-exports shows readers that they are external.

## Acceptable Globs

```rust
#[cfg(unix)]
mod sys_unix {
    pub fn page_size() -> usize { 4096 }
}

#[cfg(windows)]
mod sys_windows {
    pub fn page_size() -> usize { 4096 }
}

// One platform module is forwarded as a whole
#[cfg(unix)]
pub use sys_unix::*;
#[cfg(windows)]
pub use sys_windows::*;
```

## See Also

- [proj-pub-use-reexport](proj-pub-use-reexport.md) - Use `pub use` for a clean public API
- [proj-pub-crate-internal](proj-pub-crate-internal.md) - Keep internals out of the public surface
- [api-dont-leak-types](api-dont-leak-types.md) - Be careful which foreign types you re-export
- Source: Microsoft Pragmatic Rust Guidelines, M-NO-GLOB-REEXPORTS and M-DOC-INLINE
