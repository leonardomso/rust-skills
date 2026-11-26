# async-clone-before-await

> Clone the `Arc` handle, not its contents, before moving it into a spawned task; keep owned handles across `.await` and borrow after it

## Why It Matters

"Clone before `.await`" is easy to over-apply. Three different constraints get confused:

1. **`tokio::spawn` needs a `'static` future.** A task can't borrow the caller's locals, so it must own what it uses. The fix is `Arc::clone(&data)`, an O(1) refcount bump, moved into the `async move` block. It is not a deep copy of the data.
2. **An owned `Arc<T>` already lives across `.await`.** If an `async fn` owns `data: Arc<Data>`, the handle keeps the allocation alive through every suspension point. Deep-cloning `data.items` first adds an O(n) copy and makes every suspended future bigger, and it buys nothing.
3. **Whether a future is `Send` depends on what it holds, not on cloning.** Anything live across an `.await` is stored in the future. A `!Send` value such as `Rc<T>` or `std::sync::MutexGuard<T>` makes the whole future `!Send`. Cloning an `Rc` gives you another `!Send` `Rc`. To fix it, drop the value before the `.await` or use a `Send` type. A plain `&T` borrowed from an owned `Arc<T>` is fine when `T: Sync`.

Deep-copying the contents is right only when you need a snapshot that won't see later changes. That is a consistency decision, so label it as one.

## Bad

```rust
use std::rc::Rc;
use std::sync::Arc;

struct Data {
    items: Vec<u64>,
}

// BAD 1: the spawned task borrows the caller's local — not 'static
fn spawn_worker(data: &Data) {
    tokio::spawn(async move {
        tokio::task::yield_now().await;
        println!("{}", data.items.len()); // error: borrowed data escapes
    });
}

// BAD 2: O(n) deep copy "to be safe" even though the Arc is already owned
async fn process(data: Arc<Data>) {
    let items = data.items.clone(); // copies the whole Vec, held across the await
    tokio::task::yield_now().await;
    println!("{}", items.len());
}

// BAD 3: cloning an Rc does not make the future Send
async fn not_send() {
    let rc = Rc::new(vec![1, 2, 3]);
    let rc2 = Rc::clone(&rc); // still Rc, still !Send
    tokio::task::yield_now().await;
    println!("{rc2:?}");
}
// tokio::spawn(not_send()); // error[E0277]: `Rc<Vec<i32>>` cannot be sent between threads safely
```

## Good

```rust
use std::sync::Arc;

struct Data {
    items: Vec<u64>,
}

// Clone the handle (O(1)) and move it into the task
fn spawn_worker(data: &Arc<Data>) -> tokio::task::JoinHandle<usize> {
    let data = Arc::clone(data);
    tokio::spawn(async move {
        tokio::task::yield_now().await;
        data.items.len() // the task owns its handle; no copy of `items`
    })
}

// The owned Arc already survives the await: no clone at all
async fn process(data: Arc<Data>) -> u64 {
    tokio::task::yield_now().await;
    data.items.iter().sum() // borrow after the await
}
```

## Fix Ladder

Use the cheapest option that works:

```rust
use std::sync::Arc;

struct LargeData {
    small_field: String,
    blob: Vec<u8>,
}

// 1. Best: keep the owned Arc across the await, borrow after it
async fn zero_copy(data: Arc<LargeData>) -> usize {
    tokio::task::yield_now().await;
    data.small_field.len() + data.blob.len()
}

// 2. Need only a small piece and want the big allocation freed during a long
//    wait? Extract the piece, then drop the handle before suspending
async fn extract_part(data: Arc<LargeData>) -> usize {
    let small = data.small_field.clone();
    drop(data); // the last handle going away frees `blob` before the await
    tokio::task::yield_now().await;
    small.len()
}

// 3. Deep clone only for snapshot semantics — e.g. you must act on exactly the
//    value you validated even if a writer swaps it meanwhile. Consider
//    `arc_swap::ArcSwap` for that instead of copying per task.
```

## The Send Problem

`Rc` uses non-atomic refcounts, so it is `!Send` whether or not you clone it. Use `Arc` if shared ownership has to cross an `.await`, or keep the `Rc` in a block that ends before the await:

```rust
use std::rc::Rc;
use std::sync::Arc;

// Arc<T> is Send + Sync when T: Send + Sync
async fn with_arc() -> usize {
    let shared = Arc::new(vec![1, 2, 3]);
    tokio::task::yield_now().await;
    shared.len()
}

// Scope the !Send value so it is dropped before the suspension point
async fn with_scoped_rc() -> usize {
    let len = {
        let rc = Rc::new(vec![1, 2, 3]);
        rc.len()
    }; // `rc` dropped here
    tokio::task::yield_now().await;
    len
}

fn assert_send<F: Send>(_: F) {}

fn check() {
    assert_send(with_arc());
    assert_send(with_scoped_rc());
}
```

`Rc` held across `.await` is fine only on single-threaded executors (`LocalSet`, `spawn_local`, a current-thread runtime with `!Send` tasks).

## Spawn Pattern

Write `Arc::clone(&shared)` rather than `shared.clone()` so readers can see it is a refcount bump and not a deep copy:

```rust
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};

struct SharedState {
    hits: AtomicU64,
}

async fn fan_out() {
    let shared = Arc::new(SharedState { hits: AtomicU64::new(0) });
    let mut tasks = tokio::task::JoinSet::new();

    for _ in 0..10 {
        let shared = Arc::clone(&shared); // O(1) handle per task
        tasks.spawn(async move {
            tokio::task::yield_now().await;
            shared.hits.fetch_add(1, Ordering::Relaxed);
        });
    }
    tasks.join_all().await;
}
```

## MutexGuard Across Await

A `std::sync::MutexGuard` is `!Send`, so holding one across `.await` makes the future `!Send`. A `tokio::sync::Mutex` guard is `Send`, but holding it across I/O makes every other task wait. Take what you need inside a block so the guard is dropped before the await:

```rust
use std::sync::{Arc, Mutex};

struct Counter {
    value: u64,
    label: String,
}

async fn bump(mutex: Arc<Mutex<Counter>>) -> String {
    let label = {
        let mut guard = mutex.lock().expect("counter mutex poisoned");
        guard.value += 1;
        guard.label.clone() // copy out only what is needed after unlocking
    }; // guard dropped here: the future stays Send

    tokio::task::yield_now().await;
    label
}
```

## See Also

- [async-no-lock-await](async-no-lock-await.md) - Lock guards across await
- [own-arc-shared](own-arc-shared.md) - Arc usage patterns
- [own-borrow-over-clone](own-borrow-over-clone.md) - Borrow instead of deep-cloning
- [async-joinset-structured](async-joinset-structured.md) - Managing spawned tasks
- [async-future-size](async-future-size.md) - Keep hot futures small
