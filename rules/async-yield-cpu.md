# async-yield-cpu

> Bound CPU work on executor threads; consume cooperative budget or move sustained work to a compute pool

## Why It Matters

A future that performs a long computation without reaching a suspension point
can monopolize an executor worker. Unconditional yielding after every tiny item
solves starvation by replacing it with scheduler overhead. Define a bounded
chunk or time budget, yield through the runtime's cooperative mechanism, and
move sustained or parallel CPU work off the async executor.

## Bad

```rust
async fn transform(items: &[Vec<u8>]) -> Vec<Vec<u8>> {
    let mut output = Vec::new();
    for item in items {
        output.push(expensive_transform(item));
    }
    output
}

fn expensive_transform(item: &[u8]) -> Vec<u8> {
    item.to_vec()
}
```

A sufficiently large or expensive batch prevents unrelated tasks on that
worker from being polled.

## Good

```rust
async fn transform(items: &[Vec<u8>]) -> Vec<Vec<u8>> {
    let mut output = Vec::with_capacity(items.len());
    for chunk in items.chunks(64) {
        output.extend(chunk.iter().map(|item| expensive_transform(item)));

        // Tokio consumes cooperative budget and yields only when exhausted.
        tokio::task::consume_budget().await;
    }
    output
}

fn expensive_transform(item: &[u8]) -> Vec<u8> {
    item.to_vec()
}
```

The chunk size is a measured latency/throughput policy, not a universal
constant. A runtime-neutral library should put the cooperative operation
behind its runtime adapter instead of exposing Tokio in its public API.

## Sustained Work

Use `spawn_blocking` with explicit admission bounds for unavoidable
synchronous calls. Use a fixed compute pool for sustained or parallel CPU
work. Cooperative yielding keeps a short mixed workload responsive; it does
not add capacity or make unbounded CPU work safe.

## Key Points

- Measure worst-case uninterrupted execution, not only item count.
- Yield at a bounded chunk or runtime budget boundary, never after every cheap
  operation by default.
- Tokio's `has_budget_remaining()` only observes budget. Use
  `consume_budget().await` when a pure computation must participate in its
  cooperative scheduler.
- Bound admission to compute pools so overload becomes backpressure instead of
  an unbounded task or thread queue.
- Do not hold locks or transactions across a cooperative yield.
- Test tail latency and throughput under concurrent load before fixing a chunk
  size in policy.

## See Also

- [async-spawn-blocking](async-spawn-blocking.md) - isolate sustained CPU or blocking work
- [async-bounded-channel](async-bounded-channel.md) - apply admission backpressure
- [async-no-lock-await](async-no-lock-await.md) - release guards before yielding
- [perf-profile-first](perf-profile-first.md) - measure the scheduling trade-off
