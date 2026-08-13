# perf-batch-throughput

> Optimize for items finished per CPU cycle with batches, independent slices, and no idle spinning

## Why It Matters

A library that looks snappy on one record can still be expensive at fleet scale: each item pays a lock, a task hop, or a cache miss, and most of those cycles produce nothing. Treat *items per CPU cycle* as a primary throughput metric. Latency still matters — extra machines raise volume, they do not shrink one request's wait — but do not buy that wait-time with idle cores, one-record APIs, or contended shared state. Batching is a tool, not a law: a single interactive request with a latency SLO should not sit in a queue just to look batched.

## Bad

```rust
use std::sync::Mutex;

pub fn take_one(queue: &Mutex<Vec<u32>>) -> Option<u32> {
    queue.lock().unwrap().pop()
}

pub fn spin_for_one(queue: &Mutex<Vec<u32>>) -> u32 {
    loop {
        if let Some(item) = take_one(queue) {
            return item;
        }
        // Burns a core waiting for a single record.
    }
}

pub fn score_each(items: &[u32], scores: &Mutex<u64>) {
    for item in items {
        // Lock and (in a runtime) a task switch per record.
        *scores.lock().unwrap() += u64::from(*item);
    }
}
```

## Good

```rust
use std::collections::VecDeque;
use std::time::Duration;

pub fn score_slice(items: &[u32]) -> u64 {
    items.iter().copied().map(u64::from).sum()
}

/// Partitioning sketch: hand each returned slice to one long-lived worker.
pub fn score_chunks(items: &[u32], workers: usize) -> u64 {
    let width = items.len().div_ceil(workers.max(1)).max(1);
    items.chunks(width).map(score_slice).sum()
}

/// Public batch surface: callers who already have many records should not
/// have to loop `score_one`.
pub fn score_batch(items: &[u32]) -> u64 {
    score_slice(items)
}

pub fn take_batch(queue: &mut VecDeque<u32>, max: usize) -> Vec<u32> {
    let n = queue.len().min(max);
    queue.drain(..n).collect()
}

pub fn idle_when_empty(empty: bool) {
    if empty {
        // A real receiver should block on its channel/condition variable.
        // A bounded sleep demonstrates that the empty path does not spin.
        std::thread::sleep(Duration::from_millis(1));
    }
}

/// Cheap to recompute: sharing a mutex here would cost more than the add.
pub fn tag_len(bytes: &[u8]) -> usize {
    bytes.len()
}

fn main() {
    let items = [1u32, 2, 3, 4];
    assert_eq!(score_chunks(&items, 2), 10);
    assert_eq!(score_batch(&items), 10);
    let mut queue = VecDeque::from([9, 8, 7]);
    let batch = take_batch(&mut queue, 2);
    assert_eq!(batch, [9, 8]);
    idle_when_empty(queue.is_empty());
    assert_eq!(tag_len(b"ab"), 2);
}
```

## Key Points

- Track how many records finish per CPU cycle; do not spend that budget on idle waits, a lock per record, or a task switch per record.
- Slice work up front. Give each thread or task its own chunk and let it run without coordinating on every item.
- Offer batched APIs and call batched APIs when they exist. Walk records one-by-one only when a batch is impossible or would miss a latency SLO.
- Park, sleep, or yield when the queue is empty. Do not busy-wait for the next item.
- Yield inside a long item, or between slices of a batch, so one chunk cannot pin a worker (`async-yield-cpu`).
- Keep each slice in contiguous memory so the next record is already in cache.
- Do not steal or re-queue *individual* records to "balance" load; move whole slices if you must rebalance.
- Share mutable state only when the share is cheaper than recomputing. Otherwise recompute on the stack.

## See Also

- [async-yield-cpu](async-yield-cpu.md) - yield inside a long item or between batch slices
- [opt-cache-friendly](opt-cache-friendly.md) - keep each slice on contiguous, hot data
- [own-mutex-interior](own-mutex-interior.md) - a lock per record is usually more expensive than recomputing
- [perf-profile-first](perf-profile-first.md) - batching is not automatically faster; measure the actual cost
