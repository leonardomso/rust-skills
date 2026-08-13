# proj-avoid-statics

> Do not store mutable or process-identity state in `static`; pass it in. Reserve `static` for immutable tables

## Why It Matters

A `static` looks unique. Cargo can link two major versions of the same crate into one binary, and each copy gets its own `static`. Counters, registries, and "the" logger then split silently. Mutable statics also fight tests: every test shares one cell. a `static` is allowed only when a second copy would not change the answer — lookup tables, interned strings, atomics used purely as a fast path. Edition 2024 already rejects `static mut`; `clippy::disallowed_types` / workspace `banned` lists can keep `lazy_static` and ad-hoc globals out of libraries.

The same identity warning applies to thread-local state: every linked crate
version and every thread gets another copy. A `0.x` crate makes this especially
easy because each minor line is a distinct compatibility version. Shared
mutable statics also become cache-line and lock contention points in
thread-per-core designs; pass cell-local state through a service handle.

## Bad

```rust
use std::sync::atomic::{AtomicUsize, Ordering};

static HITS: AtomicUsize = AtomicUsize::new(0);

pub fn record_hit() -> usize {
    HITS.fetch_add(1, Ordering::Relaxed)
}
```

## Good

```rust
use std::sync::atomic::{AtomicUsize, Ordering};

pub struct HitCounter {
    hits: AtomicUsize,
}

impl HitCounter {
    pub const fn new() -> Self {
        Self {
            hits: AtomicUsize::new(0),
        }
    }

    pub fn record(&self) -> usize {
        self.hits.fetch_add(1, Ordering::Relaxed)
    }
}

// Immutable table: a second copy would still return the same bytes.
static CRC_NIBBLE: [u8; 16] = [0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0];

pub fn parity_nibble(n: u8) -> u8 {
    CRC_NIBBLE[(n & 0x0f) as usize]
}

fn main() {
    let counter = HitCounter::new();
    assert_eq!(counter.record(), 0);
    assert_eq!(parity_nibble(3), 0);
}
```

## See Also

- [const-vs-static](const-vs-static.md) - `const` for inlined values; `static` only when you need an address
- [conc-thread-local](conc-thread-local.md) - thread-locals are still process-global per thread
- [test-mock-traits](test-mock-traits.md) - inject clocks, entropy, and I/O instead of reading them from a static
