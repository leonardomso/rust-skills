# async-durable-worker

> Claim durable work atomically, bound retries with backoff and jitter, and make worker shutdown explicit

## Why It Matters

An in-memory spawned task disappears on process crash. A loop that polls an
empty database without delay creates load while doing nothing. A worker that
deletes a task before completing the side effect loses work; one that never
records attempts retries poison tasks forever. Store work durably and model the
claim, lease, completion, retry, and dead-letter transitions.

## Contract

- Enqueue business state and the work record in one local transaction (outbox
  pattern).
- Claim a bounded batch atomically using a lease/visibility timeout or database
  locking that allows other workers to skip claimed rows.
- Make task processing idempotent because a crash can occur after the side
  effect but before acknowledgement.
- Acknowledge/delete only after the success condition is durable.
- Classify permanent versus transient failures. Retry transient failures with
  capped exponential backoff and jitter, honoring an attempt and age budget.
- Move exhausted or permanent failures to a queryable dead-letter state with
  operator context.
- Block, notify, or sleep when the queue is empty; never hot-poll.
- Observe queue depth, oldest age, attempts, success/failure rate, and worker
  heartbeat.
- On shutdown, stop claiming, finish or release leases within a deadline, and
  join the worker task.

## Good State Model

```rust
pub enum WorkState {
    Pending,
    Leased { attempt: u32 },
    Completed,
    DeadLetter,
}

pub fn retry_delay(base_ms: u64, attempt: u32, jitter_ms: u64) -> u64 {
    base_ms
        .saturating_mul(1_u64 << attempt.min(16))
        .saturating_add(jitter_ms)
}

fn main() {
    assert_eq!(retry_delay(100, 3, 7), 807);
}
```

## Failure Tests

- crash before claim, after claim, after side effect, and before acknowledge;
- lease expiry makes abandoned work visible again;
- two workers never own the same live lease;
- empty queues do not generate unbounded queries;
- poison work reaches dead-letter after the exact attempt budget;
- cancellation releases or completes in-flight work according to policy.

## See Also

- [async-bounded-channel](async-bounded-channel.md) - bound in-process handoff
- [async-cancellation-token](async-cancellation-token.md) - coordinate shutdown
- [async-joinset-structured](async-joinset-structured.md) - retain and join worker tasks
- [api-idempotency-key](api-idempotency-key.md) - make repeated side-effect attempts safe
- [conc-db-transaction-boundary](conc-db-transaction-boundary.md) - atomically enqueue outbox work
