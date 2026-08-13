# async-join-parallel

> Join a small fixed set of independent, cancellation-safe futures

## Why It Matters

`join!` polls several futures concurrently on the current task; it does not create tasks or CPU parallelism. It can reduce wall time when independent operations spend time pending, but latency is not guaranteed to equal the slowest isolated operation because they contend for downstream capacity and executor time. `try_join!` returns on the first observed error and drops the unfinished branch futures. Use it only when those futures are cancellation-safe or when partial progress is an accepted part of the contract.

## Bad

```rust
async fn load_dashboard() -> Result<Dashboard, Error> {
    let user = fetch_user().await?;
    let posts = fetch_posts().await?;
    let alerts = fetch_alerts().await?;
    Ok(Dashboard { user, posts, alerts })
}
```

This is correct when each step depends on the previous one. It is needlessly sequential only when the three calls are genuinely independent and simultaneous load is admitted downstream.

## Good

```rust
use tokio::try_join;

async fn load_dashboard() -> Result<Dashboard, Error> {
    let (user, posts, alerts) = try_join!(
        fetch_user(),
        fetch_posts(),
        fetch_alerts(),
    )?;
    Ok(Dashboard { user, posts, alerts })
}
```

The three clients must have bounded deadlines, cancellation-safe futures, and enough connection/concurrency capacity for this fan-out. A failed branch drops the other two branch futures at the next return from `try_join!`; it does not roll back effects already committed by them.

## `join!` Versus `try_join!`

```rust
use tokio::{join, try_join};

let (left, right) = join!(infallible_left(), infallible_right());
let (left, right) = try_join!(fallible_left(), fallible_right())?;
```

- `join!` waits for every branch and returns every output, including errors as ordinary output values.
- `try_join!` returns the first error it observes and drops remaining branch futures.
- Both store and poll branches in one parent future. A branch that performs long CPU work without yielding can starve its siblings.
- Tokio's default polling rotates the first branch for fairness; `biased;` fixes poll order and requires the author to prove that high-volume branches cannot starve shutdown or control branches.
- Neither macro supplies a timeout, retry policy, rollback, tracing span, or admission limit.

## Dynamic Collections Need A Limit

```rust
use futures::{stream, StreamExt, TryStreamExt};
use std::num::NonZeroUsize;

async fn fetch_users(
    ids: Vec<u64>,
    limit: NonZeroUsize,
) -> Result<Vec<User>, Error> {
    stream::iter(ids)
        .map(|id| async move { fetch_user(id).await })
        .buffered(limit.get()) // Keeps input order; use buffer_unordered if order is irrelevant.
        .try_collect()
        .await
}
```

Do not build an unbounded `join_all` or `try_join_all` from request-controlled input. The concurrency limit is an end-to-end policy derived from downstream quotas, connection pools, per-tenant fairness, memory, and retry amplification. Bound the input count before constructing futures. `buffered` stops polling after an error is returned through `try_collect`, so branch cancellation requirements still apply.

## CPU Work Is Not Parallelized

```rust
async fn wrong_for_cpu(inputs: &[Input]) -> Vec<Output> {
    let (a, b) = tokio::join!(
        async { cpu_transform(&inputs[0]) },
        async { cpu_transform(&inputs[1]) },
    );
    vec![a, b]
}
```

Both transformations run on the same task and can monopolize one executor worker. Send sustained CPU work through bounded admission to a fixed compute pool. Do not create one `spawn_blocking` job per untrusted input.

## Dependent Or Transactional Work

Keep operations sequential when later inputs depend on earlier outputs. When independent branches cause external effects, define compensation/idempotency before concurrent execution. `try_join!` is not an atomic transaction: one branch can commit before another fails. For durable multi-step workflows, persist state transitions and make retries replay-safe.

## Failure And Shutdown Contract

- Set an overall request deadline and compatible per-branch deadlines.
- Preserve branch error identity; do not report only whichever error happened to be observed first without correlation.
- Instrument fan-out size, active branches, downstream saturation, cancellations, and tail latency.
- On shutdown, stop admission first and give owned tasks a bounded drain period. Plain joined futures are owned by their caller and are cancelled when that caller is dropped.
- Test cancellation at each await point and inject one-branch failure after another branch has made progress.

## See Also

- [async-try-join](./async-try-join.md) - preserve errors and cancellation semantics
- [async-select-racing](./async-select-racing.md) - race branches only when losers are safe to cancel
- [async-joinset-structured](./async-joinset-structured.md) - supervise dynamically spawned tasks
- [async-bounded-channel](async-bounded-channel.md) - enforce admission backpressure
