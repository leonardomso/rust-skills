# api-service-clone

> Expose long-lived services as cheap `Clone` handles around `Arc<Inner>`, not as fat values callers must wrap themselves

## Why It Matters

A server constructs one client, one clock, one telemetry sink, and then needs that same instance in a dozen handlers. If `Clone` deep-copies the service, callers invent their own `Arc` and your type leaks into every signature. Model a service as a handle: `Clone` bumps a refcount and methods forward to `Inner`. That is an API convention, not the same claim as "use `Arc` when you share" (`own-arc-shared`).

## Bad

```rust
pub struct Catalog {
    pub items: Vec<String>,
}

impl Catalog {
    pub fn new(items: Vec<String>) -> Self {
        Self { items }
    }

    pub fn len(&self) -> usize {
        self.items.len()
    }
}

fn fan_out(catalog: Catalog) -> usize {
    // Each clone copies the Vec. Callers will wrap this in Arc themselves.
    let a = catalog.clone();
    a.len()
}

impl Clone for Catalog {
    fn clone(&self) -> Self {
        Self {
            items: self.items.clone(),
        }
    }
}
```

## Good

```rust
use std::sync::Arc;

struct CatalogInner {
    items: Vec<String>,
}

#[derive(Clone)]
pub struct Catalog {
    inner: Arc<CatalogInner>,
}

impl Catalog {
    pub fn new(items: Vec<String>) -> Self {
        Self {
            inner: Arc::new(CatalogInner { items }),
        }
    }

    pub fn len(&self) -> usize {
        self.inner.items.len()
    }
}

fn fan_out(catalog: &Catalog) -> usize {
    let a = catalog.clone();
    let b = catalog.clone();
    a.len() + b.len()
}

fn main() {
    let catalog = Catalog::new(vec!["a".into(), "b".into()]);
    assert_eq!(fan_out(&catalog), 4);
}
```

## Compose Shared Services

Construct dependent services from a shared service bundle by reference and
clone only the cheap handles they retain:

```rust
#[derive(Clone)]
pub struct Services {
    pub catalog: Catalog,
}

#[derive(Clone)]
pub struct Search {
    catalog: Catalog,
}

impl Search {
    pub fn new(services: &Services) -> Self {
        Self { catalog: services.catalog.clone() }
    }
}
```

If a dependency is used only during `new`, do not retain it. Build one service
instance per worker or application cell and clone handles into request
handlers; do not reconstruct deep service graphs per request.

## See Also

- [own-arc-shared](own-arc-shared.md) - the `Arc` mechanics this handle is built on
- [api-no-wrapper-params](api-no-wrapper-params.md) - keep the `Arc` inside the handle, not in every parameter
- [api-common-traits](api-common-traits.md) - `Clone` is part of the public contract for a handle
