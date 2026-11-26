# own-rwlock-readers

> Use `RwLock<T>` when reads significantly outnumber writes

## Why It Matters

`Mutex<T>` allows only one thread to access data at a time, even for reads. `RwLock<T>` allows multiple concurrent readers OR one exclusive writer. For read-heavy workloads, this dramatically improves throughput by eliminating unnecessary serialization of read operations.

## Bad

```rust
use std::sync::{Arc, Mutex};

// Configuration rarely changes but is read constantly
let config = Arc::new(Mutex::new(Config::load()));

// Every read blocks other reads unnecessarily
fn get_setting(config: &Mutex<Config>, key: &str) -> String {
    let guard = config.lock().unwrap();
    guard.get(key).to_string()
}

// 100 threads reading = serialized, one at a time
```

## Good

```rust
use std::sync::{Arc, RwLock};

// Multiple readers can proceed concurrently
let config = Arc::new(RwLock::new(Config::load()));

fn get_setting(config: &RwLock<Config>, key: &str) -> String {
    let guard = config.read().unwrap(); // Multiple threads can hold read lock
    guard.get(key).to_string()
}

fn update_setting(config: &RwLock<Config>, key: &str, value: &str) {
    let mut guard = config.write().unwrap(); // Exclusive access for writes
    guard.set(key, value);
}

// 100 threads reading = parallel execution
```

## parking_lot::RwLock

Prefer `parking_lot::RwLock` for better performance:

```rust
use parking_lot::RwLock;
use std::sync::Arc;

let data = Arc::new(RwLock::new(HashMap::new()));

// Read - no unwrap needed
let value = data.read().get("key").cloned();

// Write
data.write().insert("key".to_string(), "value".to_string());

// Upgradeable read lock (unique to parking_lot)
let upgradeable = data.upgradable_read();
if upgradeable.get("key").is_none() {
    let mut write = parking_lot::RwLockUpgradableReadGuard::upgrade(upgradeable);
    write.insert("key".to_string(), "default".to_string());
}
```

## When RwLock Hurts

RwLock has overhead for tracking readers. It can be slower than Mutex when:

| Scenario | Better Choice |
|----------|---------------|
| Writes are frequent (>20% of operations) | `Mutex` |
| Lock held very briefly | `Mutex` |
| Single-threaded | `RefCell` |
| Reads dominate, lock held longer | `RwLock` |

## Fairness and Write Starvation

`std::sync::RwLock` does not promise a priority policy; it depends on the OS implementation. A steady stream of readers may starve a waiting writer on some platforms, and a waiting writer may block new readers on others. `parking_lot::RwLock` documents a task-fair policy that avoids both reader and writer starvation. If fairness matters, pick a lock that documents the policy you need.

## Downgrading a Write Lock

`RwLockWriteGuard::downgrade` (stable since Rust 1.92) turns a write guard into a read guard atomically, so no other writer can get in between. This is about atomicity, not fairness. It lets you publish a value and then keep reading it without a window where another writer can change it:

```rust
use std::sync::{RwLock, RwLockWriteGuard};

fn refresh_and_read(lock: &RwLock<Vec<u32>>) -> usize {
    let mut writer = lock.write().expect("lock poisoned");
    writer.push(42);
    // atomically become a reader: other readers may now enter, writers may not
    let reader = RwLockWriteGuard::downgrade(writer);
    reader.len()
}
```

## Real-World Pattern: Cached Computation

```rust
use parking_lot::RwLock;
use std::sync::Arc;

struct CachedData {
    cache: RwLock<Option<ExpensiveResult>>,
}

impl CachedData {
    fn get(&self) -> ExpensiveResult {
        // Fast path: read lock
        if let Some(cached) = self.cache.read().as_ref() {
            return cached.clone();
        }
        
        // Slow path: compute and cache
        let result = compute_expensive();
        *self.cache.write() = Some(result.clone());
        result
    }
}
```

## See Also

- [own-mutex-interior](./own-mutex-interior.md) - When writes are frequent
- [async-no-lock-await](./async-no-lock-await.md) - RwLock in async contexts
