# mem-arrayvec

> Use `ArrayVec<T, N>` when the collection itself needs fixed inline capacity

## Why It Matters

`ArrayVec` from the `arrayvec` crate provides a Vec-like API with a
compile-time maximum capacity and stores its elements inline wherever the
`ArrayVec` value lives. The collection does not allocate storage when it fills,
but an element type may allocate internally. Exceeding capacity either returns
an error through a checked method or panics through an infallible method. Use it
when the capacity is a real contract, not as a silent truncation mechanism.

## Bad

```rust
// A non-empty Vec ordinarily allocates separate element storage.
fn parse_options(input: &str) -> Vec<Option> {
    let mut options = Vec::new();  // Heap allocation
    for part in input.split(',').take(8) {  // Know we never exceed 8
        options.push(parse_option(part));
    }
    options
}

// Or SmallVec when you truly can't exceed capacity
use smallvec::SmallVec;
fn get_flags() -> SmallVec<[Flag; 4]> {
    // SmallVec CAN heap-allocate if pushed beyond 4
    // That might be unexpected in no-alloc contexts
}
```

## Good

```rust
use arrayvec::ArrayVec;

// Reject input that exceeds the documented capacity.
fn parse_options(input: &str) -> Result<ArrayVec<Option<u32>, 8>, &'static str> {
    let mut options = ArrayVec::new();
    for part in input.split(',') {
        options
            .try_push(parse_option(part))
            .map_err(|_| "at most eight options are allowed")?;
    }
    Ok(options)
}

// In a #![no_std] crate:
fn collect_readings() -> ArrayVec<SensorReading, 16> {
    let mut readings = ArrayVec::new();
    for sensor in SENSORS.iter() {
        readings.push(sensor.read());  // Panics if > 16
    }
    readings
}
```

## ArrayVec vs SmallVec vs Vec

| Type | Element storage | Use When |
|------|-----------------|----------|
| `Vec<T>` | Separate allocation when capacity is nonzero | Unknown size, may grow |
| `SmallVec<[T; N]>` | Inline through N, then separate allocation | Usually small, occasionally large |
| `ArrayVec<T, N>` | Inline and fixed at N | Hard limit is part of the contract |

## API Patterns

```rust
use arrayvec::ArrayVec;

let mut arr: ArrayVec<i32, 4> = ArrayVec::new();

// Push with potential panic (like Vec)
arr.push(1);
arr.push(2);

// Safe push - returns Err if full
match arr.try_push(3) {
    Ok(()) => println!("Added"),
    Err(err) => println!("Full, couldn't add {}", err.element()),
}

// Check capacity
assert!(arr.len() < arr.capacity());

// Remaining capacity
let remaining = arr.remaining_capacity();

// Is it full?
if arr.is_full() {
    arr.pop();
}

// From iterator with limit
let arr: ArrayVec<_, 10> = (0..100)
    .filter(|x| x % 2 == 0)
    .take(10)  // Important: don't exceed capacity
    .collect();
```

## ArrayString for Inline Strings

```rust
use arrayvec::ArrayString;
use std::fmt::Write; // brings the write! target trait into scope

// Inline string with max capacity
let mut s: ArrayString<64> = ArrayString::new();
s.push_str("Hello, ");
s.push_str("world!");

// ArrayString itself uses inline storage
fn format_code(code: u32) -> ArrayString<16> {
    let mut s = ArrayString::new();
    write!(&mut s, "CODE-{:04}", code).unwrap();
    s
}
```

## When NOT to Use ArrayVec

```rust
// ❌ When size varies widely
fn parse_json_array(json: &str) -> ArrayVec<Value, ???> {
    // What capacity? JSON arrays can be any size
}

// ❌ When capacity is very large
let big: ArrayVec<u8, 1_000_000> = ArrayVec::new();  // 1MB on stack = bad

// ✅ Use SmallVec or Vec instead for these cases
```

## Cargo.toml

```toml
[dependencies]
arrayvec = "0.7"
```

## See Also

- [mem-smallvec](./mem-smallvec.md) - When heap fallback is acceptable
- [mem-with-capacity](./mem-with-capacity.md) - Pre-allocating Vec capacity
- [own-move-large](./own-move-large.md) - Large stack types considerations
