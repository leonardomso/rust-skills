# api-avoid-statics

> Pass correctness-relevant state explicitly instead of keeping it in a library's `static` items

## Why It Matters

Cargo can link several semver-incompatible versions of one crate into the same binary, and each copy gets its own `static`. State that must be consistent, such as a counter, registry, or "initialized" flag, then silently splits in two, and the two halves disagree. Statics also leak state between unit tests and become contention points under load. Statics used only as a cache or performance optimization are fine, because a wrong value there is harmless.

## Bad

```rust
use std::sync::atomic::{AtomicU64, Ordering};

// If two versions of this crate are linked, there are two counters
static NEXT_ID: AtomicU64 = AtomicU64::new(1);

pub fn next_id() -> u64 {
    NEXT_ID.fetch_add(1, Ordering::Relaxed)
}
```

## Good

```rust
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};

// The caller owns the state and decides how widely to share it
#[derive(Clone)]
pub struct IdGenerator {
    next: Arc<AtomicU64>,
}

impl IdGenerator {
    pub fn new() -> Self {
        Self { next: Arc::new(AtomicU64::new(1)) }
    }

    pub fn next_id(&self) -> u64 {
        self.next.fetch_add(1, Ordering::Relaxed)
    }
}
```

## See Also

- [const-vs-static](const-vs-static.md) - When a `static` is appropriate
- [conc-thread-local](conc-thread-local.md) - Thread-local state has the same duplication issue
- [test-fixture-raii](test-fixture-raii.md) - Isolated state keeps tests independent
- Source: Microsoft Pragmatic Rust Guidelines, M-AVOID-STATICS
