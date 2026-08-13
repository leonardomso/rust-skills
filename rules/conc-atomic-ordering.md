# conc-atomic-ordering

> Use the weakest correct memory `Ordering` for every atomic operation

## Why It Matters

Defaulting to `SeqCst` on every atomic can impose unnecessary ordering and
obscure the synchronization proof, but the concrete cost depends on operation,
architecture, compiler, and surrounding code. Choosing an ordering that is too
weak can expose stale or inconsistent state and, when non-atomic memory is
involved, can permit a data race and undefined behavior. Write the
happens-before argument first, use a mutex when that argument is not small and
reviewable, and benchmark only after correctness.

## Bad

```rust
use std::sync::atomic::{AtomicU64, AtomicBool, Ordering};

static COUNTER: AtomicU64 = AtomicU64::new(0);
static READY: AtomicBool = AtomicBool::new(false);
static mut DATA: u64 = 0;

// SeqCst everywhere obscures the intended independent counter and handoff.
fn increment() {
    COUNTER.fetch_add(1, Ordering::SeqCst);
}

fn producer() {
    // SAFETY: this example is intentionally bad. Concurrent access to DATA
    // needs a proven synchronization protocol.
    unsafe { DATA = 42; }
    READY.store(true, Ordering::SeqCst); // overkill for a single flag
}

fn consumer() -> Option<u64> {
    if READY.load(Ordering::SeqCst) {
        // SAFETY: SeqCst on READY can provide the handoff here, but raw mutable
        // global state is needlessly hard to audit; use the atomic payload below.
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
// consumer loads a value written by that Release (Acquire) and then observes
// the operations sequenced before the publishing store.
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
| `Acquire` | Load/RMW that reads from a release sequence and must observe operations before it |
| `Release` | Store/RMW that publishes preceding operations to an acquiring reader |
| `AcqRel` | Read-modify-write (e.g. `compare_exchange`) acting as both Acquire and Release |
| `SeqCst` | Need a single global order observed by all threads across multiple atomic variables |

## Verification with loom

Use the `loom` crate to explore ordering choices for small concurrent units
within an explicit bounded model. A green model proves only the instrumented
state space you supplied:

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

- [conc-atomic-update](conc-atomic-update.md) - replace hand-written compare-exchange retry loops
- [own-mutex-interior](own-mutex-interior.md) - prefer `Mutex<T>` when lock-free isn't required
- [test-loom-concurrency](test-loom-concurrency.md) - explore a bounded instrumented concurrency model
- [conc-scoped-threads](conc-scoped-threads.md) - safely share stack data across threads
