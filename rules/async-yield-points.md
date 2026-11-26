# async-yield-points

> Add `yield_now().await` points to long CPU-bound loops in async code so they do not starve other tasks

## Why It Matters

An async task only gives up its thread at an `.await` that returns `Pending`. A loop that does CPU work without I/O never reaches one, so every other task on that worker waits until the loop ends. Yield at regular intervals so the runtime can schedule other work. Pick an interval where the cost of a task switch is small compared with the work done between yields; tens of microseconds of work per yield is a reasonable starting point.

## Bad

```rust
async fn checksum_all(blobs: &[Vec<u8>]) -> u64 {
    let mut total = 0u64;
    // No await point: this task holds its worker thread until the loop ends
    for blob in blobs {
        total = total.wrapping_add(checksum(blob));
    }
    total
}

fn checksum(bytes: &[u8]) -> u64 {
    bytes.iter().map(|&b| u64::from(b)).sum()
}
```

## Good

```rust
use tokio::task::yield_now;

const ITEMS_PER_YIELD: usize = 64;

async fn checksum_all(blobs: &[Vec<u8>]) -> u64 {
    let mut total = 0u64;
    for (i, blob) in blobs.iter().enumerate() {
        total = total.wrapping_add(checksum(blob));
        // Hand the thread back every so often
        if (i + 1) % ITEMS_PER_YIELD == 0 {
            yield_now().await;
        }
    }
    total
}

fn checksum(bytes: &[u8]) -> u64 {
    bytes.iter().map(|&b| u64::from(b)).sum()
}
```

## Notes

- A loop that already awaits I/O on each iteration yields on its own; add explicit yields only for CPU-bound stretches.
- If one unit of work can take milliseconds or more, move it to a blocking thread instead. See [async-spawn-blocking](async-spawn-blocking.md).
- Tune `ITEMS_PER_YIELD` by measuring, not by guessing. Yielding too often wastes time on task switches.

## See Also

- [async-spawn-blocking](async-spawn-blocking.md) - Move heavy CPU work off the async workers
- [async-tokio-runtime](async-tokio-runtime.md) - Runtime configuration and worker threads
- [conc-rayon-par-iter](conc-rayon-par-iter.md) - Data parallelism for CPU-bound work
- Source: Microsoft Pragmatic Rust Guidelines, M-YIELD-POINTS
