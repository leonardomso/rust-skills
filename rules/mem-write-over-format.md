# mem-write-over-format

> Write into a reused buffer with `write!()` instead of calling `format!()` in loops and hot paths

## Why It Matters

`format!()` always allocates a new `String`. In hot paths or loops these allocations add up. `write!()` writes into an existing buffer and reuses its capacity, which removes most allocator overhead. The exact gain depends on string length, allocator, and hardware, so measure with [criterion](https://crates.io/crates/criterion).

## Bad

```rust
fn log_event(event: &Event, output: &mut Vec<u8>) {
    // format! allocates a new String every call
    let line = format!("[{}] {}: {}\n", event.timestamp, event.level, event.message);
    output.extend_from_slice(line.as_bytes());
}

fn build_url(base: &str, path: &str, params: &[(&str, &str)]) -> String {
    let mut url = format!("{}{}", base, path);
    for (key, value) in params {
        url = format!("{}{}={}&", url, key, value);  // new allocation each time
    }
    url
}
```

## Good

```rust
use std::fmt::Write;

fn log_event(event: &Event, output: &mut Vec<u8>) {
    use std::io::Write;
    // write! to Vec<u8> directly, no intermediate allocation
    write!(output, "[{}] {}: {}\n", event.timestamp, event.level, event.message).unwrap();
}

fn build_url(base: &str, path: &str, params: &[(&str, &str)]) -> String {
    let mut url = String::with_capacity(base.len() + path.len() + params.len() * 20);
    url.push_str(base);
    url.push_str(path);
    for (key, value) in params {
        // write! into the existing String, reusing its capacity
        write!(url, "{}={}&", key, value).unwrap();
    }
    url
}

// Reuse one buffer across iterations
fn render_all(items: &[Item]) {
    let mut buf = String::with_capacity(64);
    for item in items {
        buf.clear();
        write!(&mut buf, "{}: {}", item.name, item.value).unwrap();
        process(&buf);
    }
}
```

## Write Trait Varieties

- `std::fmt::Write` targets `String`.
- `std::io::Write` targets `Vec<u8>`, `File`, `TcpStream`, and so on.
- Writing to a `String` or `Vec` never fails, but `write!` still returns a `Result`, so call `.unwrap()` (or `?`).
- `writeln!` appends the newline for you.

## Skip Formatting Entirely

When the pieces are already strings, `push_str` and `push` do no formatting work.

```rust
fn greet_to_buf(name: &str, buffer: &mut String) {
    buffer.clear();
    buffer.push_str("Hello, ");
    buffer.push_str(name);
    buffer.push('!');
}
```

Since Rust 1.98, `NumBuffer` and the integer method `format_into` write a decimal number into a stack buffer and return a `&str`, with no allocation and no `fmt` dispatch. Use it when you only need the digits.

```rust
use std::fmt::NumBuffer;

fn push_id(out: &mut String, id: u32) {
    let mut buf = NumBuffer::new();
    out.push_str(id.format_into(&mut buf));
}
```

## Let the Caller Own the Buffer

Implement `Display` so callers format into their own buffer instead of receiving a new `String`.

```rust
use std::fmt::{self, Write};

struct Event { level: u8, message: String }

impl fmt::Display for Event {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[{}] {}", self.level, self.message)
    }
}

fn render(events: &[Event]) -> Result<String, fmt::Error> {
    let mut buf = String::new();
    for e in events {
        writeln!(buf, "{}", e)?;
    }
    Ok(buf)
}
```

## When format! Is Fine

```rust
// One-time formatting, not in a loop
let message = format!("Starting server on port {}", port);

// Return value (can't return a reference to a local buffer)
fn describe(item: &Item) -> String {
    format!("{}: {}", item.name, item.value)
}

// Error and debug paths
let err = format!("invalid input: {}", input);
```

## See Also

- [mem-avoid-format](./mem-avoid-format.md) - General format! avoidance patterns
- [mem-reuse-collections](./mem-reuse-collections.md) - Reusing buffers in loops
- [mem-with-capacity](./mem-with-capacity.md) - Pre-allocating string capacity
- [obs-log-overhead](obs-log-overhead.md) - Keep telemetry cheap on hot paths
