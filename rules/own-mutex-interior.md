# own-mutex-interior

> Use `Mutex<T>` for interior mutability across threads

## Why It Matters

When you need shared mutable state across threads, `Mutex<T>` provides safe interior mutability with synchronization. Unlike `RefCell`, `Mutex` is `Send + Sync` and uses OS-level locking to ensure only one thread can access the data at a time.

## Bad

```rust
use std::cell::RefCell;
use std::sync::Arc;

// RefCell is !Sync - this won't compile
let shared = Arc::new(RefCell::new(vec![]));

// ERROR: RefCell cannot be shared between threads safely
std::thread::spawn({
    let shared = shared.clone();
    move || shared.borrow_mut().push(1)
});
```

## Good

```rust
use std::sync::{Arc, Mutex};

let shared = Arc::new(Mutex::new(vec![]));

let handles: Vec<_> = (0..10).map(|i| {
    let shared = shared.clone();
    std::thread::spawn(move || {
        let mut data = shared.lock().unwrap();
        data.push(i);
    })
}).collect();

for handle in handles {
    handle.join().unwrap();
}

println!("{:?}", shared.lock().unwrap()); // All values present
```

## Mutex Poisoning

If a thread panics while holding a lock, the mutex becomes "poisoned":

```rust
use std::sync::{Arc, Mutex};

let mutex = Arc::new(Mutex::new(0));

// Handle poisoning gracefully
match mutex.lock() {
    Ok(guard) => println!("Value: {}", *guard),
    Err(poisoned) => {
        // Recover the data anyway
        let guard = poisoned.into_inner();
        println!("Recovered value: {}", *guard);
    }
}

// Or ignore poisoning (use with caution)
let guard = mutex.lock().unwrap_or_else(|e| e.into_inner());
```

## Consider parking_lot::Mutex

`parking_lot::Mutex` is a popular alternative with a different API:

```rust
use parking_lot::Mutex;
use std::sync::Arc;

let shared = Arc::new(Mutex::new(vec![]));

// No poisoning, no Result to unwrap
let mut data = shared.lock();
data.push(42);
// Lock automatically released when guard drops
```

How it differs from `std::sync::Mutex`:
- No poisoning: `lock()` returns the guard directly instead of a `LockResult`, so it is not a drop-in replacement; call sites change
- Its raw lock is one byte. `std`'s size depends on platform, toolchain, and `T` (for example, `size_of::<std::sync::Mutex<()>>()` is 8 on Linux x86_64 today), so measure with `size_of` on your targets instead of assuming
- Eventual fairness, plus `MutexGuard::unlock_fair` when you need a strict hand-off
- Performance under contention differs by platform and workload; `std` has used futex-based locks on Linux since Rust 1.62. Benchmark before switching for speed alone

## When to Use What

| Type | Threading | Overhead | Use Case |
|------|-----------|----------|----------|
| `RefCell<T>` | Single | Minimal | Interior mutability, same thread |
| `Mutex<T>` | Multi | Locking | Shared mutable state across threads |
| `RwLock<T>` | Multi | Locking | Many readers, few writers |
| `parking_lot::Mutex` | Multi | Locking | No poisoning, `lock()` returns the guard directly |

## See Also

- [own-rwlock-readers](./own-rwlock-readers.md) - When reads dominate writes
- [own-refcell-interior](./own-refcell-interior.md) - Single-threaded alternative
- [async-no-lock-await](./async-no-lock-await.md) - Avoiding locks across await points
- [conc-atomic-ordering](./conc-atomic-ordering.md) - Lock-free alternative for simple state
