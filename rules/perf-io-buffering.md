# perf-io-buffering

> Wrap `Read`/`Write` in `BufReader`/`BufWriter` for many small operations

## Why It Matters

Small `Read` or `Write` calls on an unbuffered OS file or socket can each reach
the kernel. Byte-at-a-time loops may therefore issue enormous numbers of
syscalls. `BufReader` and `BufWriter` batch those operations, but another
buffering layer is redundant for an already buffered transport and write
buffering changes flush and latency behavior. Measure the actual adapter and
workload before choosing a non-default capacity.

## Bad

```rust
use std::fs::File;
use std::io::{Read, Write};

// Every read call goes to the OS — catastrophic for line-by-line processing
fn count_lines_slow(path: &str) -> std::io::Result<usize> {
    let mut file = File::open(path)?;
    let mut count = 0usize;
    let mut byte = [0u8; 1];
    loop {
        match file.read(&mut byte) { // one syscall per byte
            Ok(0) => break,
            Ok(_) => {
                if byte[0] == b'\n' {
                    count += 1;
                }
            }
            Err(e) => return Err(e),
        }
    }
    Ok(count)
}

// Writing many small records without buffering — each write is a syscall
fn write_records_slow(path: &str, records: &[String]) -> std::io::Result<()> {
    let mut file = File::create(path)?;
    for record in records {
        file.write_all(record.as_bytes())?; // one syscall per record
        file.write_all(b"\n")?;             // another syscall
    }
    Ok(())
}
```

## Good

```rust
use std::fs::File;
use std::io::{self, BufRead, BufReader, BufWriter, Write};

// BufReader batches OS reads; lines() still produces one owned String per line
fn count_lines_fast(path: &str) -> io::Result<usize> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let mut count = 0usize;
    for line in reader.lines() {
        line?; // propagate IO errors
        count += 1;
    }
    Ok(count)
}

// BufWriter batches writes; explicit flush() surfaces errors that drop() would swallow
fn write_records_fast(path: &str, records: &[String]) -> io::Result<()> {
    let file = File::create(path)?;
    let mut writer = BufWriter::new(file);
    for record in records {
        writer.write_all(record.as_bytes())?;
        writer.write_all(b"\n")?;
    }
    writer.flush()?; // MUST flush explicitly — drop() swallows flush errors
    Ok(())
}

// Custom buffer size when the default 8 KiB isn't optimal
fn process_large_file(path: &str) -> io::Result<()> {
    let file = File::open(path)?;
    let reader = BufReader::with_capacity(64 * 1024, file); // 64 KiB buffer
    for line in reader.lines() {
        let _line = line?;
        // process...
    }
    Ok(())
}
```

## Key Points

- `BufWriter::flush()?` must be called explicitly. When a `BufWriter` is dropped, it attempts to flush, but any resulting error is **silently discarded**. Always flush before the writer goes out of scope.
- Buffer capacity is an implementation detail and can change between Rust releases. A larger buffer can improve sequential throughput, but it also increases per-connection memory.
- `BufReader` implements `BufRead`, which provides `lines()`, `read_line()`, and `read_until()` — use these instead of reading bytes manually.
- Network streams may benefit from buffering many small writes, but protocol framing and latency requirements determine when to flush.
- If you wrap a type that is already internally buffered (e.g., `tokio::io::BufWriter` in async code), adding another layer is redundant.

## See Also

- [mem-with-capacity](mem-with-capacity.md) - pre-size buffers when the final size is known
- [perf-profile-first](perf-profile-first.md) - confirm IO is the bottleneck before tuning
