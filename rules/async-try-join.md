# async-try-join

> Use `try_join!` only when unfinished branches are safe to drop on error

## Why It Matters

`try_join!` polls a fixed set of fallible futures concurrently in one parent task. When a branch returns `Err`, the macro returns that error and drops unfinished branch futures. Dropping a future stops polling it; it does not roll back completed effects, run arbitrary async cleanup, or guarantee cancellation of an underlying blocking syscall or remote request. The primary design question is therefore cancellation and partial effects, not “fail fast” alone.

## Bad

```rust
async fn create_both() -> Result<(), Error> {
    tokio::try_join!(
        create_external_account(),
        charge_payment_method(),
    )?;
    Ok(())
}
```

One branch can commit while the other fails. Returning one error does not make the pair transactional and may lose the information needed to compensate or resume.

## Good

```rust
use tokio::try_join;

async fn load_inputs() -> Result<(Config, Policy), Error> {
    // Both operations are read-only, deadline-bounded, and cancellation-safe.
    let (config, policy) = try_join!(load_config(), load_policy())?;
    Ok((config, policy))
}
```

For externally visible effects, persist a workflow state or outbox record, assign idempotency keys, and make every step replayable before adding concurrency.

## Preserve Error Context

```rust
use anyhow::Context;

async fn load_inputs() -> anyhow::Result<(Config, Policy)> {
    let (config, policy) = tokio::try_join!(
        async { load_config().await.context("load configuration") },
        async { load_policy().await.context("load policy") },
    )?;
    Ok((config, policy))
}
```

The returned error is the first one observed in polling order, not necessarily the only or earliest real-world failure. Add correlation and branch identity. Do not log secrets, credentials, raw tenant payloads, or unrestricted paths as context.

## Deadlines

```rust
use std::time::Duration;
use tokio::time::timeout;

async fn fetch_pair() -> Result<(A, B), Error> {
    let joined = async {
        tokio::try_join!(
            async {
                timeout(Duration::from_secs(2), fetch_a())
                    .await
                    .map_err(|_| Error::Deadline("a"))?
            },
            async {
                timeout(Duration::from_secs(2), fetch_b())
                    .await
                    .map_err(|_| Error::Deadline("b"))?
            },
        )
    };

    timeout(Duration::from_secs(3), joined)
        .await
        .map_err(|_| Error::Deadline("overall"))?
}
```

Per-branch deadlines protect individual dependencies; an overall deadline caps the composed operation. They must fit the caller's remaining budget. A timeout drops the future and is effective only when the underlying operation is cancellation-safe or independently bounded.

## Dynamic Input

Do not use `try_join_all` over request-controlled or otherwise unbounded input. It constructs and polls the whole collection concurrently. Validate the item count, then use a bounded stream:

```rust
use futures::{stream, StreamExt, TryStreamExt};

async fn fetch_users(ids: Vec<u64>) -> Result<Vec<User>, Error> {
    const MAX_IDS: usize = 1_000;
    const CONCURRENCY: usize = 16;

    if ids.len() > MAX_IDS {
        return Err(Error::TooManyIds);
    }

    stream::iter(ids)
        .map(|id| async move { fetch_user(id).await })
        .buffered(CONCURRENCY)
        .try_collect()
        .await
}
```

Choose the limit from downstream quotas, connection-pool capacity, per-tenant fairness, retry amplification, and memory. If output order is irrelevant, `buffer_unordered` can reduce head-of-line blocking.

## Cancellation Contract

A branch used with `try_join!` should document what dropping it can leave behind:

- read-only async I/O should release permits, buffers, and connection state safely;
- protocol streams must remain reusable or be discarded after cancellation;
- blocking work needs its own deadline/isolation because dropping the wrapper may not stop it;
- durable effects require idempotency and persisted progress;
- cleanup that must await cannot rely on `Drop` and needs an owned supervisor or explicit compensation path.

Test cancellation at every relevant await point and inject failure after peer branches make partial progress.

## Collecting Every Result

Use `join!` for a small fixed tuple when every result must be observed. For a bounded dynamic set, consume a bounded stream and collect or report each result explicitly. “Best effort” still needs a success threshold, retry/dead-letter policy, bounded diagnostic cardinality, and a returned summary; silently filtering failures is not production error handling.

## See Also

- [async-join-parallel](./async-join-parallel.md) - bound fan-out and distinguish concurrency from parallelism
- [async-select-racing](./async-select-racing.md) - prove loser cancellation safety
- [async-cancel-safety](async-cancel-safety.md) - test drop behavior at await boundaries
- [api-idempotency-key](api-idempotency-key.md) - make repeated effects replay-safe
