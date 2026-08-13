# test-loom-concurrency

> Use bounded `loom` models to explore lock-free and concurrent code

## Why It Matters

Probabilistic stress tests can run millions of iterations and still miss a race
that needs one specific interleaving. `loom` systematically explores schedules
and memory-ordering choices for its instrumented primitives within configured
model bounds. A green model proves the asserted property only for that model,
state space, and loom-backed implementation—not for every production input,
platform primitive, or uninstrumented code path. Tokio uses loom as one layer
when verifying synchronization primitives.

## Bad

```rust
// Stress test: might pass a billion times, still doesn't prove correctness
#[test]
fn stress_test_flag() {
    use std::sync::{Arc, atomic::{AtomicBool, Ordering}};
    let flag = Arc::new(AtomicBool::new(false));
    for _ in 0..1_000_000 {
        let flag = Arc::clone(&flag);
        std::thread::spawn(move || {
            flag.store(true, Ordering::Relaxed);
        });
    }
    // races may never surface under the OS scheduler used here
}
```

## Good

Gate concurrent primitives behind `#[cfg(loom)]` so the same code runs with loom's instrumented types during model checking and with std types in production:

```rust
// src/flag.rs
#[cfg(loom)]
use loom::sync::atomic::{AtomicBool, Ordering};
#[cfg(not(loom))]
use std::sync::atomic::{AtomicBool, Ordering};

pub struct Flag(AtomicBool);

impl Flag {
    pub const fn new() -> Self {
        Self(AtomicBool::new(false))
    }

    pub fn set(&self) {
        self.0.store(true, Ordering::Release);
    }

    pub fn is_set(&self) -> bool {
        self.0.load(Ordering::Acquire)
    }
}
```

```rust
// tests/loom_flag.rs  (or inside a #[cfg(loom)] mod in the crate)
#[cfg(loom)]
mod tests {
    use loom::sync::Arc;
    use super::Flag;

    #[test]
    fn flag_set_visible_to_other_thread() {
        loom::model(|| {
            let flag = Arc::new(Flag::new());

            let flag2 = Arc::clone(&flag);
            let writer = loom::thread::spawn(move || {
                flag2.set();
            });

            // Within this model, the reader may run before or after the writer.
            let seen = flag.is_set();
            writer.join().expect("modeled writer panicked");

            // After join, writer must have completed; flag must be set.
            assert!(flag.is_set(), "flag must be set after join");
            // 'seen' may be false if reader ran before writer — that is valid.
            let _ = seen;
        });
    }
}
```

Declare the custom cfg to rustc and run the model explicitly:

```bash
RUSTFLAGS="--cfg loom --check-cfg=cfg(loom)" cargo test --test loom_flag
```

## Key Points

- Keep loom model closures **small**: combinatorial explosion grows with the number of atomic operations and threads. Test one primitive or algorithm at a time.
- loom replaces `std::sync::atomic`, `std::sync::Mutex`, `std::thread`, and `std::cell` with instrumented equivalents — import from `loom::` under `#[cfg(loom)]`.
- Use `loom::model(|| { ... })` as the entry point; loom runs the closure repeatedly under different schedules.
- Model bounds, branch limits, and state-space reductions are part of the test contract; record them when they exclude reachable production behavior.
- loom does not detect logical bugs unrelated to concurrency or prove that the `cfg(not(loom))` implementation is structurally identical.

## See Also

- [conc-atomic-ordering](conc-atomic-ordering.md) - choose correct memory orderings
- [test-criterion-bench](test-criterion-bench.md) - benchmark concurrent code after verifying correctness
