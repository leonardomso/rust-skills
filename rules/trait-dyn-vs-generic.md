# trait-dyn-vs-generic

> Choose concrete types, enums, generics, or `dyn Trait` from the substitution and ownership contract

## Why It Matters

Dispatch is an API decision, not a universal performance ladder. Concrete types
are simplest when behavior is fixed. Enums model a closed set. Generics keep
open implementations statically dispatched but can spread type parameters
through public state. Trait objects provide runtime heterogeneity, smaller code,
and a stable erased boundary at the cost of object-safety constraints and
indirect calls.

Do not translate every interface from another language into `Arc<dyn Trait>`.
Do not hide a genuine ownership-and-erasure contract merely to ban `dyn` from a
public signature.

## Bad

```rust
use std::sync::Arc;

pub trait Store {
    fn load(&self, key: &str) -> Option<Vec<u8>>;
}

// There is one implementation, but every caller inherits sharing and dispatch.
pub struct Service {
    store: Arc<dyn Store + Send + Sync>,
}
```

## Good

Use the least complex form that expresses the supported substitutions.

### Concrete Type

```rust
pub struct Store;

impl Store {
    pub fn load(&self, _key: &str) -> Option<Vec<u8>> {
        None
    }
}

pub struct Service {
    store: Store,
}
```

Choose this when the implementation is fixed and callers do not supply one.

### Closed Enum

```rust
pub enum Backend {
    Memory(MemoryStore),
    File(FileStore),
}

pub struct MemoryStore;
pub struct FileStore;
```

Choose this when the supported set is intentionally closed and exhaustive
matching is useful.

### Generic Parameter

```rust
pub trait Store {
    fn load(&self, key: &str) -> Option<Vec<u8>>;
}

pub struct Service<S> {
    store: S,
}

impl<S: Store> Service<S> {
    pub fn load(&self, key: &str) -> Option<Vec<u8>> {
        self.store.load(key)
    }
}
```

Choose this when callers provide implementations and the parameter remains
local instead of infecting many public types.

### Trait Object

```rust
pub trait Store: Send + Sync {
    fn load(&self, key: &str) -> Option<Vec<u8>>;
}

pub struct Service {
    store: Box<dyn Store>,
}

impl Service {
    pub fn new(store: Box<dyn Store>) -> Self {
        Self { store }
    }
}
```

A public `Box<dyn Store>` is appropriate when the caller transfers unique
ownership of an erased implementation. `Arc<dyn Store>` is appropriate when
shared ownership itself is the contract. A crate-owned handle can hide those
wrappers when storage and sharing are implementation details that may change.

## Decision Guide

| Requirement | Default |
|---|---|
| One implementation | Concrete type |
| Small, closed implementation set | Enum |
| Caller implementations; type remains local | Generic / `impl Trait` |
| Runtime heterogeneous collection | `dyn Trait` |
| Stable plugin or ABI-adjacent erasure boundary | `dyn Trait` behind an owned boundary |
| Sharing is internal | Crate-owned cloneable handle |
| Caller transfers or shares erased ownership | Public `Box` / `Arc<dyn Trait>` may be the honest API |

## Key Points

- Keep traits narrow and based on behavior callers actually substitute.
- Require `Send` and `Sync` only when the execution contract needs them.
- Confirm object safety before committing to `dyn Trait`.
- Benchmark dispatch only on measured hot paths; monomorphization also has code
  size and compile-time costs.
- Avoid nested generic architecture that exposes implementation topology.
- State ownership directly. Hiding every smart pointer can make lifetime and
  sharing costs less clear rather than more stable.

## See Also

- [api-no-wrapper-params](api-no-wrapper-params.md) - keep incidental wrappers out of signatures
- [api-service-clone](api-service-clone.md) - hide internal shared ownership in a handle
- [anti-type-erasure](anti-type-erasure.md) - retain known concrete types
- [anti-over-abstraction](anti-over-abstraction.md) - do not add substitution without a consumer
- [trait-object-safety](trait-object-safety.md) - requirements for `dyn Trait`
- [type-generic-bounds](type-generic-bounds.md) - keep bounds near their use
