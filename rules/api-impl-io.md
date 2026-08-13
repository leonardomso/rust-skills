# api-impl-io

> Accept `impl Read` / `impl Write` (or the async equivalents) instead of a concrete file or socket

## Why It Matters

A function that takes `std::fs::File` cannot parse bytes that arrived over the network, from stdin, or from a test cursor without first writing them to disk. Sans-I/O APIs take the standard I/O traits and let the caller supply the source. That yields N×M composability: one parser, many transports. Use this for one-shot reads or writes, especially during initialization. For asynchronous libraries that target multiple runtimes, accept `futures::io::AsyncRead` / `AsyncWrite` or a crate-owned port instead of a Tokio-specific type. A long-lived runtime-aware service needs an explicit runtime adapter, not a borrowed stream parameter threaded through every method.

## Bad

```rust
use std::fs::File;
use std::io::Read;

pub fn decode_frame(mut file: File) -> std::io::Result<Vec<u8>> {
    let mut buf = Vec::new();
    file.read_to_end(&mut buf)?;
    Ok(buf)
}
```

## Good

```rust
use std::io::{Cursor, Read};

pub fn decode_frame(mut data: impl Read) -> std::io::Result<Vec<u8>> {
    let mut buf = Vec::new();
    data.read_to_end(&mut buf)?;
    Ok(buf)
}

fn main() -> std::io::Result<()> {
    let from_memory = decode_frame(Cursor::new(b"payload"))?;
    let from_slice = decode_frame(&b"payload"[..])?;
    assert_eq!(from_memory, from_slice);
    Ok(())
}
```

## See Also

- [api-impl-asref](api-impl-asref.md) - the same flexibility for borrowed string, path, and byte inputs
- [perf-io-buffering](perf-io-buffering.md) - wrap the `Read`/`Write` you accept in a buffer at the call site
- [test-mock-traits](test-mock-traits.md) - trait inputs are what make I/O-free tests possible
- [api-impl-rangebounds](api-impl-rangebounds.md) - the same flexibility for range parameters
