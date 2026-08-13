# doc-inline-reexport

> Inline an owned re-export when rustdoc would otherwise show only a forwarding link

## Why It Matters

Rustdoc automatically inlines an item re-exported from a private module. Adding
`#[doc(inline)]` there is redundant. The attribute is useful when a public
facade deliberately re-exports an owned item from another public module or a
constituent crate and wants the facade page to contain the full documentation.
Use it only on the canonical public path; forced inlining must not disguise two
competing user-facing paths.

## Bad

```rust
mod detail {
    pub struct Client;
}

// Already inlined because `detail` is private.
#[doc(inline)]
pub use detail::Client;
```

The attribute adds no behavior and suggests the default is not understood.

## Good

```rust
#[doc(hidden)]
pub mod core {
    /// Sends requests through the configured transport.
    pub struct Client;
}

// The facade intentionally owns the documented path.
#[doc(inline)]
pub use core::Client;

fn main() {
    let _ = Client;
}
```

In a real multi-crate facade, apply the same policy to an owned constituent
crate. Do not inline arbitrary third-party types merely because they appear in
your signatures.

## Key Points

- Private-module re-exports are inlined automatically.
- Use `#[doc(inline)]` when rustdoc would otherwise retain a forwarding entry
  and the facade is the intended documentation home.
- Use `#[doc(no_inline)]` when preserving the defining path is clearer.
- Keep one supported public path for an owned item.
- Leave foreign types attributed to their defining crates unless an explicit
  facade contract says otherwise.
- Inspect generated rustdoc; this is a presentation rule, not a type-system
  invariant.

## See Also

- [proj-pub-use-reexport](proj-pub-use-reexport.md) - choose one canonical public path
- [proj-no-glob-reexport](proj-no-glob-reexport.md) - name every public re-export
- [api-std-types-boundary](api-std-types-boundary.md) - avoid accidental foreign API commitments
- [doc-all-public](doc-all-public.md) - document the item at its canonical path
