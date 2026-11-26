# conc-atomic-ordering

> Use the weakest correct memory `Ordering` for every atomic operation

## Why It Matters

Defaulting to `SeqCst` (sequentially consistent) on every atomic is a common correctness-first shortcut, but it carries real cost: on x86 the difference is small, but on ARM and RISC-V weaker orderings map to cheaper instructions while `SeqCst` requires full memory barriers. More importantly, choosing the wrong ordering — even a weaker one — is a correctness bug that causes data races the compiler won't catch. Understanding the four practical levels lets you write both correct and efficient concurrent code.

## Bad

```rust
use std::sync::atomic::{AtomicU64, AtomicBool, Ordering};

static COUNTER: AtomicU64 = AtomicU64::new(0);
static READY: AtomicBool = AtomicBool::new(false);
static mut DATA: u64 = 0;

// SeqCst everywhere — correct, but unnecessarily expensive
fn increment() {
    COUNTER.fetch_add(1, Ordering::SeqCst);
}

fn producer() {
    unsafe { DATA = 42; }
    READY.store(true, Ordering::SeqCst); // overkill for a single flag
}

fn consumer() -> Option<u64> {
    if READY.load(Ordering::SeqCst) {
        Some(unsafe { DATA })
    } else {
        None
    }
}
```

## Good

```rust
use std::sync::atomic::{AtomicU64, AtomicBool, Ordering};

static COUNTER: AtomicU64 = AtomicU64::new(0);

// Relaxed: no ordering relative to other memory — fine for independent counters
fn increment() {
    COUNTER.fetch_add(1, Ordering::Relaxed);
}

fn total() -> u64 {
    COUNTER.load(Ordering::Relaxed)
}

// Acquire/Release: paired handoff — producer writes data THEN sets flag (Release);
// consumer loads flag (Acquire) and is guaranteed to see the preceding write.
static READY: AtomicBool = AtomicBool::new(false);
static VALUE: AtomicU64 = AtomicU64::new(0);

fn producer(value: u64) {
    VALUE.store(value, Ordering::Relaxed);   // write payload first
    READY.store(true, Ordering::Release);    // publish with Release
}

fn consumer() -> Option<u64> {
    if READY.load(Ordering::Acquire) {       // synchronize with Release store
        Some(VALUE.load(Ordering::Relaxed))  // payload visible after Acquire
    } else {
        None
    }
}

// SeqCst: only when you need a single total order across *multiple* atomics.
// Example: Dekker-style mutual exclusion involving two independent flags.
```

## Ordering Quick Reference

| Ordering | Use when |
|----------|----------|
| `Relaxed` | Operation is atomic but needs no ordering relative to other memory (counters, stats) |
| `Acquire` | Load that must see all stores preceding a matching `Release` on another thread |
| `Release` | Store that must be visible before a matching `Acquire` load on another thread |
| `AcqRel` | Read-modify-write (e.g. `compare_exchange`) acting as both Acquire and Release |
| `SeqCst` | Need a single global order observed by all threads across multiple atomic variables |

## Read-Modify-Write Helpers

`AtomicXxx::update` (stable since Rust 1.95) retries a closure in a compare-exchange loop and returns the previous value. `try_update` is the same for closures that may decline by returning `None`. `fetch_update` is deprecated since Rust 1.99 in favour of `try_update`. Use the `AtomicXxx` names: the generic `Atomic<T>` they alias is still unstable.

```rust
use std::sync::atomic::{AtomicU32, Ordering};

static IN_FLIGHT: AtomicU32 = AtomicU32::new(0);
const LIMIT: u32 = 64;

/// Claims a slot, or returns `false` when the limit is reached.
fn try_acquire() -> bool {
    IN_FLIGHT
        .try_update(Ordering::Acquire, Ordering::Relaxed, |n| {
            (n < LIMIT).then_some(n + 1)
        })
        .is_ok()
}

fn release() {
    IN_FLIGHT.update(Ordering::Release, Ordering::Relaxed, |n| n - 1);
}
```

## Verification with loom

Use the `loom` crate to exhaustively verify ordering choices for small concurrent units — it explores all interleavings the C11 memory model permits:

```rust
#[cfg(loom)]
use loom::sync::atomic::{AtomicBool, Ordering};

#[cfg(loom)]
#[test]
fn test_handoff() {
    loom::model(|| {
        // ... spawn threads, assert invariants
    });
}
```

## See Also

- [own-mutex-interior](own-mutex-interior.md) - prefer `Mutex<T>` when lock-free isn't required
- [test-loom-concurrency](test-loom-concurrency.md) - exhaustively test concurrent code with loom
- [conc-scoped-threads](conc-scoped-threads.md) - safely share stack data across threads
