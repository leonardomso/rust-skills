# own-rwlock-readers

> Benchmark `RwLock<T>` for read-heavy shared state; do not assume readers make it faster

## Why It Matters

`Mutex<T>` permits one holder, while `RwLock<T>` permits multiple readers or
one writer. That extra state and coordination has a cost. A read-heavy workload
may improve when critical sections are long enough and readers actually run in
parallel, but a short critical section, cache-line contention, writer pressure,
or an oversubscribed runtime can make `RwLock` slower. Choose from measured
contention and tail latency, not a read/write percentage.

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
    let guard = config.read().expect("configuration lock poisoned");
    guard.get(key).to_string()
}

fn update_setting(config: &RwLock<Config>, key: &str, value: &str) {
    let mut guard = config.write().expect("configuration lock poisoned");
    guard.set(key, value);
}

// Readers may proceed concurrently when the scheduler and workload allow it
```

## parking_lot::RwLock

`parking_lot::RwLock` offers a smaller API and additional lock operations, but
it is a dependency and not an automatic performance win:

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
| Writes or writer latency matter | Benchmark `Mutex` and `RwLock` |
| Lock held very briefly | `Mutex` |
| Single-threaded | `RefCell` |
| Reads dominate, lock held longer | `RwLock` |

## Write Starvation

Fairness policy for `std::sync::RwLock` is platform-dependent.
`parking_lot::RwLock` uses an eventual-fairness policy, not strict FIFO.
Whichever primitive you choose, exercise writer progress under sustained read
load and record the latency objective.

```rust
// parking_lot provides explicit fair unlock operations where policy needs them
use parking_lot::RwLock;

// Or use std with explicit fairness (nightly)
// #![feature(rwlock_downgrade)]
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
