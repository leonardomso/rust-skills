# api-dont-leak-types

> Prefer `std` types in public APIs; expose third-party types only when they give a clear benefit

## Why It Matters

Every type in a public signature becomes part of your API contract. If you return a type from another crate, a breaking release of that crate forces a breaking release of yours, and callers can be left with two incompatible versions of it. Only `std` types come with a permanent stability promise. Leak a third-party type when it is the main way your users interoperate with a large part of the ecosystem, or put it behind a feature flag.

## Bad

```rust
use indexmap::IndexMap;

pub struct Headers {
    // pub field: IndexMap is now part of this crate's public API
    pub map: IndexMap<String, String>,
}

impl Headers {
    // Callers must depend on the same indexmap version to use the result
    pub fn all(&self) -> &IndexMap<String, String> {
        &self.map
    }
}
```

## Good

```rust
use indexmap::IndexMap;

#[derive(Default)]
pub struct Headers {
    // Private: the map type can change without a breaking release
    map: IndexMap<String, String>,
}

impl Headers {
    pub fn insert(&mut self, name: impl Into<String>, value: impl Into<String>) {
        self.map.insert(name.into(), value.into());
    }

    pub fn get(&self, name: &str) -> Option<&str> {
        self.map.get(name).map(String::as_str)
    }

    // Expose behavior through std traits, not the concrete map
    pub fn iter(&self) -> impl Iterator<Item = (&str, &str)> {
        self.map.iter().map(|(k, v)| (k.as_str(), v.as_str()))
    }
}
```

## When Leaking Is Fine

- The types come from a sibling crate in the same umbrella project.
- The type is exposed only behind an opt-in feature, such as a `serde` or `tokio` feature.
- The type is the shared vocabulary of the ecosystem for this problem, and avoiding it would make your API harder to use.

## See Also

- [api-newtype-safety](api-newtype-safety.md) - Wrap foreign types in your own newtype
- [api-serde-optional](api-serde-optional.md) - Put ecosystem integrations behind a feature
- [api-sealed-trait](api-sealed-trait.md) - Keep implementation details out of the contract
- [proj-pub-use-reexport](proj-pub-use-reexport.md) - Re-export deliberately
- Source: Microsoft Pragmatic Rust Guidelines, M-DONT-LEAK-TYPES
