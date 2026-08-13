# async-tokio-fs

> Isolate filesystem blocking and bound file work, bytes, and concurrency

## Why It Matters

Most general-purpose operating systems expose regular-file operations as blocking calls. `std::fs` on a Tokio worker can stall unrelated tasks. Tokio's filesystem facade ordinarily delegates those calls to its blocking pool; awaiting it keeps an async worker available but does not make the underlying syscall asynchronous or cancellable. Unbounded file counts or `read_to_end` calls can still exhaust threads, descriptors, memory, and storage bandwidth.

## Bad

```rust
async fn load_all(paths: &[std::path::PathBuf]) -> std::io::Result<Vec<String>> {
    let mut output = Vec::new();
    for path in paths {
        // Blocks a runtime worker and reads an unbounded file into memory.
        output.push(std::fs::read_to_string(path)?);
    }
    Ok(output)
}
```

## Good

```rust
use futures::{stream, StreamExt, TryStreamExt};
use std::path::{Path, PathBuf};
use tokio::io::AsyncReadExt;

const MAX_FILE_BYTES: u64 = 4 * 1024 * 1024;
const MAX_CONCURRENT_READS: usize = 8;

async fn read_bounded(path: &Path) -> std::io::Result<Vec<u8>> {
    let mut file = tokio::fs::File::open(path).await?;
    let metadata = file.metadata().await?;
    if !metadata.is_file() || metadata.len() > MAX_FILE_BYTES {
        return Err(std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            "file is not regular or exceeds the byte limit",
        ));
    }

    let capacity = usize::try_from(metadata.len())
        .map_err(|_| std::io::Error::other("file length does not fit usize"))?;
    let mut bytes = Vec::with_capacity(capacity);
    file.take(MAX_FILE_BYTES + 1).read_to_end(&mut bytes).await?;
    if bytes.len() as u64 > MAX_FILE_BYTES {
        return Err(std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            "file grew beyond the byte limit while reading",
        ));
    }
    Ok(bytes)
}

async fn read_many(paths: Vec<PathBuf>) -> std::io::Result<Vec<Vec<u8>>> {
    stream::iter(paths)
        .map(|path| async move { read_bounded(&path).await })
        .buffered(MAX_CONCURRENT_READS)
        .try_collect()
        .await
}
```

The two byte checks cover the initial metadata and growth during the read. Concurrency is an explicit service policy; tune it against file-descriptor limits, blocking-pool capacity, storage queue depth, and per-request admission. For an untrusted directory tree, validate the allowed root and symlink policy with descriptor-relative platform APIs or an isolated worker; a lexical path-prefix check is not a sandbox.

## Streaming

```rust
use tokio::io::{AsyncBufReadExt, BufReader};

async fn process_lines(path: &std::path::Path) -> std::io::Result<()> {
    let file = tokio::fs::File::open(path).await?;
    let mut lines = BufReader::new(file).lines();
    let mut seen = 0_u64;

    while let Some(line) = lines.next_line().await? {
        seen = seen
            .checked_add(u64::try_from(line.len()).unwrap_or(u64::MAX))
            .ok_or_else(|| std::io::Error::other("input byte count overflow"))?;
        if seen > MAX_FILE_BYTES {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                "input exceeds the byte limit",
            ));
        }
        process_line(&line)?;
    }
    Ok(())
}
```

Line iteration bounds retained memory but still needs a cumulative byte/record limit. Define behavior for invalid UTF-8, overlong records, partial writes, disk-full, permission changes, and file replacement during processing.

## Writes And Durability

```rust
use tokio::io::AsyncWriteExt;

async fn write_temp(path: &std::path::Path, bytes: &[u8]) -> std::io::Result<()> {
    let mut file = tokio::fs::File::create(path).await?;
    file.write_all(bytes).await?;
    file.sync_all().await?;
    Ok(())
}
```

`flush` moves buffered userspace data toward the operating system; it is not a durable-storage guarantee. Crash-safe replacement requires a same-filesystem temporary file, explicit file synchronization, an atomic rename supported by the platform/filesystem, and directory synchronization where required. Test the exact storage class and failure model rather than describing `fs::write` as durable.

## Cancellation And Shutdown

Dropping an awaiting Tokio filesystem future may stop interest in its result but cannot be assumed to cancel a blocking syscall already running. Apply admission before scheduling, bound every operation, track shutdown, and wait only for a defined grace period. For hard deadlines or hostile filesystems, isolate work in a supervised process that can be terminated; adding a Tokio timeout does not reclaim a stuck blocking thread.

## When `std::fs` Fits

Synchronous filesystem APIs are appropriate in a synchronous binary phase before runtime startup, or inside a bounded blocking/worker boundary whose ownership and shutdown are explicit. A current-thread runtime makes blocking more harmful, not less: one blocking call stops every task on that runtime.

## Memory Mapping

A mapping can avoid copying payload bytes for measured random-access workloads, but it introduces platform-specific lifetime and mutation hazards: truncation can fault, external writers can race readers, and unsafe mapping constructors require a stable backing-file contract. Do not recommend mmap as a generic heavy-I/O upgrade. Pin a reviewed crate, constrain file mutation, and test faults and replacement behavior.

## See Also

- [async-spawn-blocking](./async-spawn-blocking.md) - bound blocking admission and shutdown
- [async-bounded-channel](async-bounded-channel.md) - put backpressure before scheduled work
- [async-tokio-runtime](./async-tokio-runtime.md) - configure and observe runtime resources
- [err-context-chain](./err-context-chain.md) - preserve path context without leaking secrets
