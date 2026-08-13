# proj-pub-use-reexport

> Give each owned item one public path; let callers import foreign types from their defining crate

## Why It Matters

`pub use` lets you keep a deep internal tree and still offer `the_crate::Client`. Publishing the *same* item at two public paths (`the_crate::Client` *and* `the_crate::net::Client`) creates a split identity that humans and agents preserve forever. Re-exporting `bytes::Bytes` creates a second apparent owner for a foreign type. Even when that type appears in your signatures, callers should normally import it from `bytes` and declare the dependency themselves. Hide your module, re-export your item once, and leave foreign identity with its defining crate.

## Bad

```rust
pub mod net {
    pub struct Client;
}

// Two public paths for one type: `net::Client` and `Client`.
pub use net::Client;

fn main() {
    let _ = Client;
    let _ = net::Client;
}
```

## Good

```rust
mod net {
    pub struct Client;
}

pub use net::Client;

fn main() {
    let _ = Client;
}
```

## Foreign Types

Do not re-export a dependency merely because its type appears in your public
signature. Callers need that dependency to name the type coherently, and its
original path makes documentation and version diagnostics unambiguous.

Two narrow exceptions preserve one product boundary:

- an umbrella crate may re-export items from its own constituent crates;
- a facade may re-export an item from a technical split such as `foo_core`.

Generated macros may also require a stable hidden path such as
`foo::__private::DependencyType`. That path is an implementation channel, not
a second user-facing import.

## Feature-Gated Re-exports

Name every item. A feature may add re-exports; it must not glob a module into the root.

```rust
mod blocking {
    pub struct BlockingClient;
}

#[cfg(feature = "blocking")]
pub use blocking::BlockingClient;

pub struct Client;

fn main() {
    let _ = Client;
}
```

## See Also

- [proj-no-glob-reexport](proj-no-glob-reexport.md) - never `pub use foo::*` across modules
- [proj-prelude-module](proj-prelude-module.md) - a curated prelude is a deliberate opt-in import surface
- [doc-inline-reexport](doc-inline-reexport.md) - `#[doc(inline)]` the one path you chose
- [api-std-types-boundary](api-std-types-boundary.md) - most foreign types should not appear at all
- [macro-private-helpers](macro-private-helpers.md) - the hidden stable-path exception for generated code
- [api-non-exhaustive](api-non-exhaustive.md) - the public surface you flattened still needs a stability story
- [proj-pub-crate-internal](proj-pub-crate-internal.md) - keep the un-exported tree `pub(crate)`
