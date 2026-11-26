# async-try-join

> Use `try_join!` for concurrent fallible operations with early return on error

## Why It Matters

When running multiple fallible operations concurrently, `try_join!` returns `Err` as soon as any future fails, without waiting for the others. This provides fail-fast behavior while still running operations in parallel. For many operations, use `futures::future::try_join_all`.

## Bad

```rust
// Sequential - slow and no early return benefit
async fn fetch_all() -> Result<(A, B, C)> {
    let a = fetch_a().await?;  // If this fails, we wait for nothing
    let b = fetch_b().await?;  // But if this fails, we waited for A
    let c = fetch_c().await?;
    Ok((a, b, c))
}

// join! ignores errors
async fn fetch_all() -> (Result<A>, Result<B>, Result<C>) {
    let (a, b, c) = join!(fetch_a(), fetch_b(), fetch_c());
    // All complete even if first one failed
    (a, b, c)  // Now we have to handle three Results
}
```

## Good

```rust
use anyhow::Result;
use futures::future::try_join_all;
use tokio::try_join;

async fn fetch_all() -> Result<(A, B, C)> {
    // Concurrent AND fail-fast
    let (a, b, c) = try_join!(
        fetch_a(),
        fetch_b(),
        fetch_c(),
    )?;

    Ok((a, b, c))
}

// For dynamic collections
async fn fetch_users(ids: &[u64]) -> Result<Vec<User>> {
    let futures: Vec<_> = ids.iter()
        .map(|id| fetch_user(*id))
        .collect();

    try_join_all(futures).await
}

struct A;
struct B;
struct C;
struct User { id: u64 }
async fn fetch_a() -> Result<A> { Ok(A) }
async fn fetch_b() -> Result<B> { Ok(B) }
async fn fetch_c() -> Result<C> { Ok(C) }
async fn fetch_user(id: u64) -> Result<User> { Ok(User { id }) }
```

## Error Handling Patterns

```rust
use anyhow::Result;
use futures::TryFutureExt;
use futures::future::try_join_all;
use tokio::try_join;

#[derive(Debug, thiserror::Error)]
enum Error {
    #[error(transparent)]
    Io(#[from] std::io::Error),
}

// Different error types - need common error type
async fn mixed_operations() -> Result<(A, B), Error> {
    let (a, b) = try_join!(
        fetch_a().map_err(Error::from),  // Convert errors
        fetch_b().map_err(Error::from),
    )?;
    Ok((a, b))
}

// Collect all results, then handle errors
async fn all_or_nothing(ids: &[u64]) -> Result<Vec<User>> {
    try_join_all(ids.iter().map(|id| fetch_user(*id))).await
}

// Collect successes, log failures
async fn best_effort(ids: &[u64]) -> Vec<User> {
    let results = futures::future::join_all(
        ids.iter().map(|id| fetch_user(*id))
    ).await;

    results.into_iter()
        .filter_map(|r| match r {
            Ok(user) => Some(user),
            Err(e) => {
                log::warn!("Failed to fetch user: {}", e);
                None
            }
        })
        .collect()
}

struct A;
struct B;
struct User { id: u64 }
async fn fetch_a() -> Result<A, std::io::Error> { Ok(A) }
async fn fetch_b() -> Result<B, std::io::Error> { Ok(B) }
async fn fetch_user(id: u64) -> Result<User> { Ok(User { id }) }
```

## Cancellation Behavior

```rust
use anyhow::Result;
use tokio::try_join;

#[derive(Debug, thiserror::Error)]
#[error("fetch failed")]
struct Error;

// try_join! cancels remaining futures on error
async fn with_cancellation() -> Result<()> {
    // If fetch_a() fails, fetch_b() and fetch_c() are dropped
    // But "dropped" != "immediately stopped"
    // They stop at their next .await point

    try_join!(
        async {
            fetch_a().await?;
            cleanup_a().await;  // May not run if other future fails
            Ok::<_, Error>(())
        },
        async {
            fetch_b().await?;
            cleanup_b().await;  // May not run if other future fails
            Ok::<_, Error>(())
        },
    )?;

    Ok(())
}

// For guaranteed cleanup, use Drop guards or explicit handling

async fn fetch_a() -> Result<(), Error> { Ok(()) }
async fn fetch_b() -> Result<(), Error> { Ok(()) }
async fn cleanup_a() {}
async fn cleanup_b() {}
```

## With Timeout

```rust
use futures::TryFutureExt;
use tokio::time::{timeout, Duration};
use tokio::try_join;

async fn fetch_with_timeout() -> Result<(A, B), Error> {
    timeout(
        Duration::from_secs(10),
        async { try_join!(fetch_a(), fetch_b()) }
    )
    .await
    .map_err(|_| Error::Timeout)?
}

// Per-operation timeout
async fn individual_timeouts() -> Result<(A, B), Error> {
    try_join!(
        timeout(Duration::from_secs(5), fetch_a())
            .map_err(|_| Error::Timeout)
            .and_then(|r| async { r }),
        timeout(Duration::from_secs(5), fetch_b())
            .map_err(|_| Error::Timeout)
            .and_then(|r| async { r }),
    )
}

#[derive(Debug)]
enum Error { Timeout }
struct A;
struct B;
async fn fetch_a() -> Result<A, Error> { Ok(A) }
async fn fetch_b() -> Result<B, Error> { Ok(B) }
```

## try_join! vs FuturesUnordered

```rust
use anyhow::Result;
use futures::stream::{FuturesUnordered, StreamExt};
use tokio::try_join;

async fn run() -> Result<()> {
    // try_join!: wait for all, fail fast
    let (a, b, c) = try_join!(fetch(1), fetch(2), fetch(3))?;

    // FuturesUnordered: process as they complete
    let mut futures = FuturesUnordered::new();
    futures.push(fetch(1));
    futures.push(fetch(2));
    futures.push(fetch(3));

    while let Some(result) = futures.next().await {
        match result {
            Ok(data) => process(data),
            Err(e) => return Err(e),  // Can fail fast manually
        }
    }
    Ok(())
}

async fn fetch(id: u64) -> Result<u64> { Ok(id) }
fn process(_data: u64) {}
```

## See Also

- [async-join-parallel](./async-join-parallel.md) - Non-fallible concurrent futures
- [async-select-racing](./async-select-racing.md) - First-to-complete semantics
- [err-question-mark](./err-question-mark.md) - Error propagation
