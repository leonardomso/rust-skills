# async-no-lock-await

> Release `Mutex`/`RwLock` guards before `.await`: take what you need, drop the lock, do the async work, then lock briefly to write back

## Why It Matters

Holding a lock across an `.await` point can cause deadlocks and severely hurt performance. The task may be suspended while holding the lock, blocking all other tasks waiting for it - potentially indefinitely. With `std::sync::Mutex` it is worse: the guard is not `Send`, and another task polled on the same thread that tries to lock it blocks the runtime thread.

## Bad

```rust
use tokio::sync::Mutex;

async fn bad_update(state: &Mutex<State>) {
    let mut guard = state.lock().await;
    
    // BAD: Lock held across await!
    let data = fetch_from_network().await;
    
    guard.value = data;
}  // Lock finally released

// This can deadlock or starve other tasks

// WORSE: std::sync::Mutex guard held across await
async fn bad_std_mutex(data: &std::sync::Mutex<Vec<i32>>) {
    let mut guard = data.lock().unwrap();
    do_async_work().await;  // Guard held while suspended!
    guard.push(42);
}
```

## Good

```rust
use tokio::sync::Mutex;

async fn good_update(state: &Mutex<State>) {
    // Fetch data BEFORE taking the lock
    let data = fetch_from_network().await;
    
    // Lock only for the quick update
    let mut guard = state.lock().await;
    guard.value = data;
}  // Lock released immediately

// Alternative: Clone data out, process, then update
async fn good_update_v2(state: &Mutex<State>) {
    // Extract what we need
    let id = {
        let guard = state.lock().await;
        guard.id.clone()
    };  // Lock released!
    
    // Do async work without lock
    let data = fetch_by_id(id).await;
    
    // Quick update
    state.lock().await.value = data;
}
```

## The Problem Visualized

```rust
// Task A:
let guard = mutex.lock().await;    // Acquires lock
expensive_io().await;              // Suspended, still holding lock!
// ... many milliseconds pass ...
drop(guard);                       // Finally releases

// Task B, C, D:
let guard = mutex.lock().await;    // All blocked waiting for A!
```

## Patterns for Extraction

```rust
use tokio::sync::Mutex;

// Pattern 1: Clone out, process, update
async fn pattern_clone(state: &Mutex<State>) {
    let config = state.lock().await.config.clone();
    let result = process_with_io(&config).await;
    state.lock().await.result = result;
}

// Pattern 2: Compute closure, apply
async fn pattern_closure(state: &Mutex<State>) {
    let update = compute_update().await;
    
    state.lock().await.apply(update);
}

// Pattern 3: Message passing
async fn pattern_message(
    state: &Mutex<State>,
    tx: mpsc::Sender<Update>,
) {
    let update = compute_update().await;
    tx.send(update).await.unwrap();
}

// Separate task handles updates
async fn state_manager(
    state: Arc<Mutex<State>>,
    mut rx: mpsc::Receiver<Update>,
) {
    while let Some(update) = rx.recv().await {
        state.lock().await.apply(update);
    }
}
```

## Using RwLock

```rust
use tokio::sync::RwLock;

async fn read_heavy(state: &RwLock<State>) {
    // Multiple readers OK, but still don't hold across await
    let value = {
        let guard = state.read().await;
        guard.value.clone()
    };
    
    // Process without lock
    let result = process(value).await;
    
    // Write lock for update
    state.write().await.result = result;
}
```

## What Can Cross an Await

| Held across `.await` | Verdict |
|----------------------|---------|
| `std::sync::Mutex`/`RwLock` guard | No: can deadlock, and the future is not `Send` |
| `tokio::sync::Mutex`/`RwLock` guard | Allowed, but blocks every other task wanting the lock |
| Owned values, `Arc<T>` | Yes |
| References | Depends on lifetime |

## std::sync::Mutex vs tokio::sync::Mutex

Prefer `std::sync::Mutex` for work that does not span an `.await`: it is simpler and faster. Reach for `tokio::sync::Mutex` only when the lock must be held across an `.await` (rare; usually a sign to redesign).

```rust
// Quick, non-awaiting operation: std Mutex is fine
async fn quick_update(state: &std::sync::Mutex<State>) {
    state.lock().unwrap().counter += 1;  // No await inside lock scope
}
```

## Detection

```toml
# Cargo.toml
[lints.clippy]
await_holding_lock = "deny"
await_holding_refcell_ref = "deny"
```

## See Also

- [async-spawn-blocking](async-spawn-blocking.md) - Use spawn_blocking for CPU work
- [own-mutex-interior](own-mutex-interior.md) - Mutex usage
- [async-clone-before-await](async-clone-before-await.md) - Clone data before await
- [api-types-send](api-types-send.md) - Make public types and futures Send
