# conc-atomic-update

> Use atomic `update` / `try_update` instead of hand-written compare-exchange loops

## Why It Matters

A compare-exchange loop must reload the value after contention, distinguish success and failure orderings, and retry without losing a concurrent update. Hand-written loops are easy to get subtly wrong. Rust 1.95 stabilized `update` and `try_update` on atomic integers, booleans, and pointers. They encode the retry loop once while leaving the state transition and memory ordering explicit.

## Bad

```rust
use std::sync::atomic::{AtomicU64, Ordering};

fn increment_below(counter: &AtomicU64, limit: u64) -> Result<u64, u64> {
    let mut current = counter.load(Ordering::Acquire);
    loop {
        if current >= limit {
            return Err(current);
        }
        match counter.compare_exchange_weak(
            current,
            current + 1,
            Ordering::AcqRel,
            Ordering::Acquire,
        ) {
            Ok(previous) => return Ok(previous),
            Err(observed) => current = observed,
        }
    }
}
```

## Good

```rust
use std::sync::atomic::{AtomicU64, Ordering};

fn increment_below(counter: &AtomicU64, limit: u64) -> Result<u64, u64> {
    counter.try_update(Ordering::AcqRel, Ordering::Acquire, |current| {
        (current < limit).then_some(current + 1)
    })
}

fn toggle(flag: &std::sync::atomic::AtomicBool) -> bool {
    flag.update(Ordering::AcqRel, Ordering::Acquire, |current| !current)
}
```

`try_update` returns `Ok(previous)` after storing the closure result. Returning `None` stops without writing and returns `Err(current)`. `update` always produces a replacement and returns the previous value.

## Key Points

- The closure may run more than once under contention. It must not perform I/O, mutate unrelated state, generate IDs, or rely on being called exactly once.
- `update` and `try_update` are compare-and-swap loops, not locks. They do not prevent ABA problems for pointer or version-like state.
- Choose success and failure orderings exactly as for `compare_exchange`; the failure ordering may be only `Relaxed`, `Acquire`, or `SeqCst`.
- Use `fetch_add`, `fetch_or`, and other dedicated operations when they express the transition directly. They are simpler and may map more closely to hardware.
- Fall back to a mutex when the transition spans multiple values or requires non-trivial side effects.

## See Also

- [conc-atomic-ordering](conc-atomic-ordering.md) - choose the weakest correct memory ordering
- [own-mutex-interior](own-mutex-interior.md) - use a mutex for compound state transitions
- [test-loom-concurrency](test-loom-concurrency.md) - explore concurrent interleavings with loom
