# api-no-wrapper-params

> Keep `Rc`, `Arc`, `Box`, and `RefCell` out of public function signatures unless sharing is the API

## Why It Matters

Smart pointers in a public signature leak an ownership scheme callers cannot change. Once two crates disagree about `Arc` versus `Rc`, or `Mutex` versus `RwLock`, the types no longer compose and the wrapper infects every downstream field. Treat incidental wrappers as implementation details: accept and return `&T`, `&mut T`, or `T`, and hide internal sharing behind the type.

## Bad

```rust
use std::cell::RefCell;
use std::rc::Rc;
use std::sync::{Arc, Mutex};

pub struct Settings {
    pub name: String,
}

pub struct Snapshot {
    pub ready: bool,
}

// Callers must already live in this exact sharing scheme.
pub fn apply_locked_settings(data: Arc<Mutex<Settings>>) -> Box<Snapshot> {
    let ready = data.lock().unwrap_or_else(|e| e.into_inner()).name.is_empty();
    Box::new(Snapshot { ready })
}

pub fn boot_from_cell(settings: Rc<RefCell<Settings>>) -> Arc<Snapshot> {
    let ready = settings.borrow().name.is_empty();
    Arc::new(Snapshot { ready })
}
```

## Good

```rust
use std::sync::Arc;

pub struct Settings {
    pub name: String,
}

pub struct Snapshot {
    ready: bool,
}

impl Snapshot {
    pub fn is_ready(&self) -> bool {
        self.ready
    }
}

// Borrow or take ownership; sharing stays inside the type if it is needed.
pub fn apply_settings(data: &Settings) -> Snapshot {
    Snapshot {
        ready: !data.name.is_empty(),
    }
}

pub fn take_settings(settings: Settings) -> Snapshot {
    Snapshot {
        ready: !settings.name.is_empty(),
    }
}

// Sharing *is* the API: a handle type, not a raw Arc in every signature.
#[derive(Clone)]
pub struct SharedSnapshot {
    inner: Arc<Snapshot>,
}

impl SharedSnapshot {
    pub fn new(state: Snapshot) -> Self {
        Self {
            inner: Arc::new(state),
        }
    }

    pub fn is_ready(&self) -> bool {
        self.inner.is_ready()
    }
}
```

## Measured Exception

A measured hot-path win can justify exposing a wrapper when callers need the
same representation and the alternative copies substantial data. Require a
benchmark and document the ownership consequence; "it might be faster" is not
an exception.

## See Also

- [own-arc-shared](own-arc-shared.md) - share with `Arc` behind a type, not in every parameter
- [api-sealed-trait](api-sealed-trait.md) - hide implementation choices that callers should not implement
- [anti-over-abstraction](anti-over-abstraction.md) - extra wrappers add type noise without adding capability
- [type-deref-coercion](type-deref-coercion.md) - do not paper over a leaked wrapper with `Deref`
- [api-service-clone](api-service-clone.md) - hide the Arc inside a Clone handle
- [api-std-types-boundary](api-std-types-boundary.md) - do not leak third-party types either
