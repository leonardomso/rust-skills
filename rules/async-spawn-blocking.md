# async-spawn-blocking

> Move blocking calls off executor threads and bound sustained CPU work

## Why It Matters

Tokio uses a small set of worker threads to poll many futures. A blocking call
or long computation on one worker delays unrelated tasks. `spawn_blocking`
moves synchronous work to Tokio's blocking pool, but that pool has a high
default thread limit because it also serves blocking I/O. It is not automatic
CPU backpressure: many CPU jobs must acquire a semaphore or enter a separately
bounded compute pool. Once a blocking task starts, aborting its `JoinHandle`
does not stop it, and runtime shutdown waits for it unless the caller imposes a
shutdown timeout.

## Bad

```rust
// BAD: Blocks the async runtime thread
async fn process_image(data: &[u8]) -> ProcessedImage {
    // CPU-intensive work on async thread!
    let resized = resize_image(data);      // Blocks!
    let compressed = compress(resized);     // Blocks!
    compressed
}

// BAD: Synchronous file I/O in async context
async fn read_large_file(path: &Path) -> Vec<u8> {
    std::fs::read(path).unwrap()  // Blocks the runtime!
}
```

## Good

```rust
use tokio::task;

use std::sync::Arc;
use tokio::sync::Semaphore;

// GOOD: Bound admission before using the blocking pool for CPU work.
async fn process_image(
    data: Vec<u8>,
    cpu_permits: Arc<Semaphore>,
) -> Result<ProcessedImage, ProcessError> {
    let permit = cpu_permits
        .acquire_owned()
        .await
        .map_err(|_| ProcessError::ShuttingDown)?;

    task::spawn_blocking(move || {
        let _permit = permit;
        let resized = resize_image(&data);
        compress(resized)
    })
    .await
    .map_err(ProcessError::Join)
}

// GOOD: Use async file I/O
async fn read_large_file(path: &Path) -> tokio::io::Result<Vec<u8>> {
    tokio::fs::read(path).await
}

// GOOD: Or spawn_blocking for unavoidable sync I/O
async fn read_with_sync_lib(path: PathBuf) -> Result<Vec<u8>, ReadError> {
    task::spawn_blocking(move || sync_library::read_file(&path))
    .await
    .map_err(ReadError::Join)?
}
```

## What Counts as Blocking

```rust
// CPU-intensive operations
- Cryptographic operations (hashing, encryption)
- Image/video processing
- Compression/decompression
- Complex parsing
- Mathematical computations

// Blocking I/O
- std::fs operations
- Synchronous database drivers
- Synchronous HTTP clients
- Thread::sleep

// Measure on the deployed runtime. There is no universal duration threshold:
// poll frequency, worker count, tail-latency budget, and arrival rate matter.
```

## Practical Examples

```rust
// Password hashing (CPU-intensive)
async fn hash_password(
    password: String,
    cpu_permits: Arc<Semaphore>,
) -> Result<String, HashError> {
    let permit = cpu_permits
        .acquire_owned()
        .await
        .map_err(|_| HashError::ShuttingDown)?;
    task::spawn_blocking(move || {
        let _permit = permit;
        bcrypt::hash(password, bcrypt::DEFAULT_COST).map_err(HashError::Hash)
    })
    .await
    .map_err(HashError::Join)?
}

// JSON parsing of large documents
async fn parse_large_json(data: String) -> Result<serde_json::Value, ParseError> {
    task::spawn_blocking(move || serde_json::from_str(&data))
    .await
    .map_err(ParseError::Join)?
    .map_err(ParseError::Json)
}

// Compression
async fn compress_data(data: Vec<u8>) -> Result<Vec<u8>, CompressError> {
    task::spawn_blocking(move || {
        let mut encoder = flate2::write::GzEncoder::new(
            Vec::new(),
            flate2::Compression::default(),
        );
        encoder.write_all(&data)?;
        encoder.finish()
    })
    .await
    .map_err(CompressError::Join)?
    .map_err(CompressError::Io)
}
```

## spawn_blocking vs spawn

```rust
// spawn: Runs async code on runtime threads
tokio::spawn(async {
    // Async code here
    some_async_operation().await;
});

// spawn_blocking: Runs sync code on blocking thread pool
tokio::task::spawn_blocking(|| {
    // Synchronous, possibly CPU-intensive code
    heavy_computation();
});

// spawn_blocking returns JoinHandle that can be awaited
let result = tokio::task::spawn_blocking(|| {
    expensive_sync_operation()
}).await?;
```

## Dedicated Compute Pools

```rust
// A service adapter owns a fixed Rayon pool (or another bounded compute pool)
// and returns completion through a oneshot channel. Request handlers submit
// only after acquiring bounded queue capacity.
```

Do not create one Rayon pool per request or layer unbounded `spawn_blocking`
jobs over an unbounded parallel iterator. Pick one owner for parallelism, set a
static worker/queue bound from CPU and memory budgets, propagate cancellation
before work starts, and make shutdown behavior observable.

## Failure Behavior

- Treat a closed semaphore or queue as shutdown/backpressure, not permission to
  run inline on the executor.
- Preserve both the inner operation error and `JoinError`; a panic or runtime
  cancellation is not a successful empty result.
- Apply deadlines at the caller, but remember that timing out the future does
  not preempt already-running blocking code. The operation itself needs a
  cancellation mechanism or process boundary when preemption is required.
- Track queue time, active workers, rejected submissions, duration, panics, and
  shutdown overruns. Bound metric labels.

## See Also

- [async-tokio-fs](async-tokio-fs.md) - Use tokio::fs for async file I/O
- [async-no-lock-await](async-no-lock-await.md) - Don't hold locks across await
- [async-yield-cpu](async-yield-cpu.md) - Yield between shorter CPU chunks that stay on the runtime
- [async-future-size](async-future-size.md) - Keep the future itself small when work stays on the runtime
