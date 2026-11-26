# api-sans-io

> Take `impl Read`/`impl Write` (or their async counterparts) instead of files or paths for one-shot I/O

## Why It Matters

A function that opens a `File` or takes a `&Path` can only be fed from disk. If the same data arrives over a socket, from stdin, or from a byte slice in a test, the caller must go through a temporary file. Accepting an I/O trait keeps the parsing or formatting logic separate from where the bytes come from, so it works with every source and sink without extra code.

## Bad

```rust
use std::fs::File;
use std::io::{BufRead, BufReader};

// Only works with files; tests need a file on disk
pub fn count_lines(file: File) -> std::io::Result<usize> {
    BufReader::new(file).lines().try_fold(0, |n, line| line.map(|_| n + 1))
}
```

## Good

```rust
use std::io::{self, BufRead, Write};

// Works with files, sockets, stdin, and &[u8]
pub fn count_lines(input: impl BufRead) -> io::Result<usize> {
    input.lines().try_fold(0, |n, line| line.map(|_| n + 1))
}

pub fn write_report(mut out: impl Write, lines: usize) -> io::Result<()> {
    writeln!(out, "lines: {lines}")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn counts_lines_in_memory() -> io::Result<()> {
        assert_eq!(count_lines(&b"a\nb\nc\n"[..])?, 3);

        let mut out = Vec::new();
        write_report(&mut out, 3)?;
        assert_eq!(out, b"lines: 3\n");
        Ok(())
    }
}
```

## Notes

- Use `std::io::Read` and `Write` for synchronous code and `futures::io::AsyncRead`/`AsyncWrite` for async code that should work on more than one runtime.
- This is for one-shot I/O. A long-lived type that owns a connection needs a runtime-specific design instead.
- A `&mut W` also implements `Write`, so callers can keep ownership of their writer.

## See Also

- [api-impl-asref](api-impl-asref.md) - Accept borrowed input generically
- [test-mock-traits](test-mock-traits.md) - Traits for dependencies make code testable
- [perf-io-buffering](perf-io-buffering.md) - Wrap readers and writers in buffers
- Source: Microsoft Pragmatic Rust Guidelines, M-IMPL-IO
