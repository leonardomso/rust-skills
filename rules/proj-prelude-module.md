# proj-prelude-module

> Prefer named imports; provide a curated prelude only when a cohesive trait-heavy API needs one

## Why It Matters

A `prelude` glob (`use foo::prelude::*`) can collide with another crate, hide
which trait enabled a method, and add names to downstream scopes in a minor
release. Most libraries should export a deliberate root and let callers name
the traits they use. A prelude is justified only when importing a small,
cohesive set of extension traits is the established way to use the API.

## Bad

```rust
// Typical client crate: a prelude whose only job is to hide four root types.
pub struct Client;
pub struct Config;
pub struct Error;

pub mod prelude {
    pub use crate::{Client, Config, Error};
}

fn main() {
    let _ = prelude::Client;
}
```

## Good

```rust
// Typical crate: named exports, no prelude module.
pub struct Client;
pub struct Config;
pub struct Error;

pub fn connect(_cfg: &Config) -> Result<Client, Error> {
    Ok(Client)
}

fn main() {
    let _ = connect(&Config);
}
```

## Import Extension Traits Explicitly

Trait-heavy APIs still do not require a prelude. Put the essential trait at a
stable named path and show that import in every example:

```rust
pub trait ParallelIterator {
    fn for_each<F: Fn(Self::Item)>(self, f: F)
    where
        Self: Sized;
    type Item;
}

impl<T> ParallelIterator for Vec<T> {
    type Item = T;

    fn for_each<F: Fn(T)>(self, f: F) {
        for item in self {
            f(item);
        }
    }
}

fn main() {
    use crate::ParallelIterator;
    vec![1, 2, 3].for_each(|_| {});
}
```

## Curated Exception

A DSL or ecosystem facade may expose `crate::prelude::*` when all exported
items are routinely needed together. Keep the list explicit, small, and
semver-reviewed; do not re-export dependencies or general-purpose names.
Documentation must also show the equivalent named imports so diagnostics and
minimal consumers have a clear path.

## See Also

- [proj-pub-use-reexport](proj-pub-use-reexport.md) - one named public path, not a glob
- [proj-no-glob-reexport](proj-no-glob-reexport.md) - wildcard public imports expand silently
- [proj-mod-by-feature](proj-mod-by-feature.md) - fix the module layout before inventing a prelude
- [api-extension-trait](api-extension-trait.md) - extension traits are the usual reason a large crate needs a prelude
