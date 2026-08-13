# own-arc-shared

> Use `Arc<T>` for shared ownership that must cross thread boundaries

## Why It Matters

`Arc` (Atomic Reference Counted) updates its ownership counts atomically, so
the same allocation can be owned from multiple threads when `T` satisfies the
required `Send`/`Sync` bounds. `Arc` does not make mutation or an otherwise
non-thread-safe `T` safe. Share immutable data directly; put mutation behind an
appropriate synchronization primitive or a message-passing boundary.

## Bad

```rust
use std::rc::Rc;
use std::thread;

let data = Rc::new(vec![1, 2, 3]);
let data_clone = Rc::clone(&data);

// ERROR: Rc cannot be sent between threads safely
thread::spawn(move || {
    println!("{:?}", data_clone);
});
```

## Good

```rust
use std::sync::Arc;
use std::thread;

let data = Arc::new(vec![1, 2, 3]);
let data_clone = Arc::clone(&data);

thread::spawn(move || {
    println!("{:?}", data_clone);  // Safe!
});

println!("{:?}", data);  // Original still accessible
```

## Arc with Mutex for Mutable Shared State

```rust
use std::sync::{Arc, Mutex};
use std::thread;

let counter = Arc::new(Mutex::new(0));
let mut handles = vec![];

for _ in 0..10 {
    let counter = Arc::clone(&counter);
    let handle = thread::spawn(move || {
        let mut num = counter.lock().unwrap();
        *num += 1;
    });
    handles.push(handle);
}

for handle in handles {
    handle.join().unwrap();
}

println!("Result: {}", *counter.lock().unwrap());
```

## Arc vs Rc Decision Tree

```
Need shared ownership?
├── No → Use owned value or references
└── Yes → Will it cross thread boundaries?
    ├── No → Use Rc<T> (cheaper, no atomic ops)
    └── Yes → Use Arc<T>
        └── Need mutation?
            ├── No → Arc<T> is enough when T: Send + Sync
            └── Yes → Arc<Mutex<T>> or Arc<RwLock<T>>
```

## Common Patterns

```rust
use std::sync::Arc;

// Shared configuration (read-only)
struct AppConfig {
    database_url: String,
    max_connections: u32,
}

fn setup_workers(config: Arc<AppConfig>) {
    for i in 0..4 {
        let config = Arc::clone(&config);
        std::thread::spawn(move || {
            println!("Worker {} using db: {}", i, config.database_url);
        });
    }
}

// Shared cache with interior mutability
use std::sync::RwLock;
use std::collections::HashMap;

type Cache = Arc<RwLock<HashMap<String, String>>>;

fn get_cached(cache: &Cache, key: &str) -> Option<String> {
    cache.read().unwrap().get(key).cloned()
}

fn set_cached(cache: &Cache, key: String, value: String) {
    cache.write().unwrap().insert(key, value);
}
```

## Performance Considerations

```rust
// Arc::clone does not clone large_data; it updates the ownership count.
let a = Arc::new(large_data);
let b = Arc::clone(&a);

// Atomic refcount updates have a different cost from Rc. Measure if cloning is
// actually hot; choose Rc from the single-threaded ownership contract first.

// Avoid cloning Arc in hot loops if possible
// Bad:
for item in items {
    let arc = Arc::clone(&shared);  // Atomic op each iteration
    process(arc, item);
}

// Better: Clone once outside loop if possible
let arc = Arc::clone(&shared);
for item in items {
    process(&arc, item);  // Pass reference
}
```

## See Also

- [own-rc-single-thread](own-rc-single-thread.md) - Use Rc for single-threaded sharing
- [own-mutex-interior](own-mutex-interior.md) - Use Mutex for interior mutability
- [async-clone-before-await](async-clone-before-await.md) - Clone Arc before await points
- [conc-scoped-threads](conc-scoped-threads.md) - Borrow stack data instead of Arc
- [unsafe-send-sync-manual](unsafe-send-sync-manual.md) - Document manual Send/Sync impls
- [api-no-wrapper-params](api-no-wrapper-params.md) - Keep Arc out of public signatures unless sharing is the API
- [api-service-clone](api-service-clone.md) - Public services are cheap Clone handles around Arc
