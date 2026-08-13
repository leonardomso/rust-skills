# own-mutex-interior

> Use `Mutex<T>` for interior mutability across threads

## Why It Matters

When you need shared mutable state across threads, `Mutex<T>` serializes access
through a guard. `Mutex<T>` is `Send` and `Sync` when `T: Send`; it does not
make a thread-affine value transferable. The standard library intentionally
does not promise a particular locking implementation, size, fairness policy,
or contention cost.

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
        let mut data = shared.lock().expect("shared vector mutex poisoned");
        data.push(i);
    })
}).collect();

for handle in handles {
    handle.join().expect("worker thread panicked");
}

println!(
    "{:?}",
    shared.lock().expect("shared vector mutex poisoned")
);
```

## Mutex Poisoning

If a thread panics while holding a lock, the mutex becomes "poisoned":

```rust
use std::sync::{Arc, Mutex};

let mutex = Arc::new(Mutex::new(0));

// Recover only if the protected value's invariant is known to remain valid.
match mutex.lock() {
    Ok(guard) => println!("Value: {}", *guard),
    Err(poisoned) => {
        // This application has an explicit invariant-repair path.
        let guard = poisoned.into_inner();
        println!("Recovered value: {}", *guard);
    }
}

// Or ignore poisoning (use with caution)
let guard = mutex.lock().unwrap_or_else(|e| e.into_inner());
```

## Consider parking_lot::Mutex Deliberately

`parking_lot::Mutex` has different poisoning, fairness, size, and performance
trade-offs. Choose it only when those semantics are desired and representative
contention measurements justify another dependency:

```rust
use parking_lot::Mutex;
use std::sync::Arc;

let shared = Arc::new(Mutex::new(vec![]));

// No poisoning, no Result to unwrap
let mut data = shared.lock();
data.push(42);
// Lock automatically released when guard drops
```

Characteristics of `parking_lot`:
- No poisoning (returns guard directly)
- Object size depends on target and crate version
- Contention performance depends on workload and platform
- Fair locking option available

## When to Use What

| Type | Threading | Overhead | Use Case |
|------|-----------|----------|----------|
| `RefCell<T>` | Single | Minimal | Interior mutability, same thread |
| `Mutex<T>` | Multi | Locking | Shared mutable state across threads |
| `RwLock<T>` | Multi | Locking | Many readers, few writers |
| `parking_lot::Mutex` | Multi | Locking | Explicit non-poisoning/fairness choice |

## See Also

- [own-rwlock-readers](./own-rwlock-readers.md) - When reads dominate writes
- [own-refcell-interior](./own-refcell-interior.md) - Single-threaded alternative
- [async-no-lock-await](./async-no-lock-await.md) - Avoiding locks across await points
- [conc-atomic-ordering](./conc-atomic-ordering.md) - Lock-free alternative for simple state
