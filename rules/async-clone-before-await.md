# async-clone-before-await

> Clone shared ownership for spawned work; do not clone merely because code awaits

## Why It Matters

An `.await` does not require every borrowed value to become owned. A reference may live across suspension when its lifetime is valid, and the resulting future can still be `Send` when every captured value satisfies the required bounds. The ownership problem appears when work must outlive the current borrow—for example, a `tokio::spawn` future normally needs `'static`. Clone an `Arc` handle before moving it into that task. Do not deep-clone state just to silence a borrow error, and do not claim that cloning `Rc` makes a future `Send`.

## Bad

```rust
use std::sync::Arc;
use tokio::task::JoinHandle;

fn spawn_process(data: &Arc<Data>) -> JoinHandle<()> {
    tokio::spawn(async move {
        // ERROR: the borrowed Arc reference escapes this function, but the
        // spawned future must own everything it retains.
        data.process().await;
    })
}
```

## Good

```rust
use std::sync::Arc;
use tokio::task::JoinHandle;

fn spawn_process(data: &Arc<Data>) -> JoinHandle<()> {
    let data = Arc::clone(data);
    tokio::spawn(async move {
        data.process().await;
    })
}
```

The task owns one additional `Arc` handle. It does not clone `Data`. `Arc<T>` is transferable only when `T` supplies the necessary `Send` and `Sync` properties.

## Borrowing Across Await Can Be Correct

```rust
async fn checksum_after_ready(data: &Data) -> u64 {
    wait_until_ready().await;
    checksum(&data.bytes)
}
```

This future borrows `Data` for its own lifetime. That is a valid contract when the caller awaits it without requiring `'static`. A shared reference is `Send` only when its referent is `Sync`; borrowing does not bypass thread-safety bounds.

## The Send Boundary

```rust
use std::rc::Rc;
use std::sync::Arc;
use std::time::Duration;

async fn local_only() {
    let value = Rc::new(42);
    tokio::time::sleep(Duration::from_millis(1)).await;
    println!("{value}");
}

// Use spawn_local on a LocalSet for the Rc future. Cloning Rc would still be
// !Send. For multi-threaded spawn, choose an Arc-backed design whose T is
// Send + Sync.
async fn movable() {
    let value = Arc::new(42);
    tokio::time::sleep(Duration::from_millis(1)).await;
    println!("{value}");
}
```

`tokio::spawn(movable())` is valid here. A real `Arc<T>` does not make the future `Send` when `T` is thread-affine, when a non-`Send` guard crosses the await, or when another captured value is non-`Send`. Assert the public future's bound when mobility is part of the API.

## Minimize Ownership Duplication

```rust
// Bad: deep-clone a large graph merely to get an owned local.
async fn wasteful(data: Arc<LargeData>) {
    let data = (*data).clone();
    async_work().await;
    use_one_field(&data.small_field);
}

// Good: retain shared ownership of the existing graph.
async fn shared(data: Arc<LargeData>) {
    async_work().await;
    use_one_field(&data.small_field);
}

// Good: clone one field only when an independent owned snapshot is required.
async fn snapshot(data: Arc<LargeData>) {
    let small = data.small_field.clone();
    async_work().await;
    use_one_field(&small);
}
```

Decide whether later work needs a live shared value or a snapshot. Those have different concurrency semantics; an `Arc` clone and a field clone are not interchangeable optimizations.

## End Guard Lifetimes Before Await

```rust
use std::sync::Arc;
use tokio::sync::Mutex;

async fn update(mutex: Arc<Mutex<Data>>) {
    let next = {
        let mut guard = mutex.lock().await;
        guard.value += 1;
        guard.value
    };

    publish(next).await;
}
```

Use a lexical scope or an explicit transformation to end lock and borrow lifetimes before unrelated I/O. Releasing and reacquiring a guard also changes atomicity; if both mutations must be one invariant, redesign the operation rather than splitting it around `.await`.

## See Also

- [async-no-lock-await](./async-no-lock-await.md) - make lock scope and atomicity explicit
- [own-arc-shared](./own-arc-shared.md) - share ownership across threads when `T` permits it
- [async-assert-send](async-assert-send.md) - compile-time `Send` checks for public futures
- [async-joinset-structured](async-joinset-structured.md) - own and supervise spawned tasks
