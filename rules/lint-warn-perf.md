# lint-warn-perf

> Enable clippy::perf for performance improvements

## Why It Matters

The `clippy::perf` lint group catches performance anti-patterns—inefficient allocations, unnecessary copies, suboptimal API usage. While not all performance issues are critical, avoiding obvious inefficiencies is good practice.

## Configuration

```rust
// In lib.rs or main.rs
#![warn(clippy::perf)]
```

Or in `Cargo.toml`:

```toml
[lints.clippy]
perf = "warn"
```

## What It Catches

### Unnecessary Allocations

```rust
// WARN: Unnecessary to_string before into
fn take_string(s: impl Into<String>) { }
take_string("hello".to_string());  // Just use: "hello"

// WARN: Box::new in return with deref coercion
fn make_trait() -> Box<dyn Trait> {
    Box::new(concrete)  // Could use Into
}

// WARN: Unnecessary vec! for iteration
for x in vec![1, 2, 3] { }  // Use array: [1, 2, 3]
```

### Inefficient Operations

```rust
// WARN (manual_retain): rebuilding a Vec with filter + collect
v = v.into_iter().filter(|x| *x > 0).collect();
// Use: v.retain(|x| *x > 0)

// WARN (iter_overeager_cloned): clone before the filter
let first = v.iter().cloned().filter(|s| s.len() > 3).next();
// Use: v.iter().find(|s| s.len() > 3).cloned()
```

### Collection Inefficiencies

```rust
// WARN: extend with a single element
vec.extend(std::iter::once(item));  // Use: vec.push(item)

// WARN: Inefficient to_vec
slice.iter().cloned().collect::<Vec<_>>()  // Use: slice.to_vec()

// WARN: Manual string concatenation
let s = format!("{}{}", a, b);  // When both are &str, use: a.to_owned() + b
```

## Notable Lints in This Group

| Lint | Improvement |
|------|-------------|
| `box_collection` | Use `Vec<T>` not `Box<Vec<T>>` |
| `manual_retain` | Use `retain` instead of filter + collect |
| `iter_overeager_cloned` | Clone after the filter, not before |
| `large_enum_variant` | Box large variants |
| `manual_memcpy` | Use slice copy methods |
| `redundant_allocation` | Remove double boxing |
| `slow_vector_initialization` | Use `vec![0; n]` |
| `unnecessary_to_owned` | Remove redundant `.to_owned()` |

## Examples

```rust
// Before (perf warnings)
fn process(input: &str) -> String {
    let parts: Vec<_> = input.split(",").collect();
    let mut result = String::new();
    for part in parts.iter() {
        if part.starts_with(" ") {
            result = result + &part.trim().to_string();
        }
    }
    result
}

// After (optimized)
fn process(input: &str) -> String {
    input.split(',')
        .filter(|part| part.starts_with(' '))
        .map(str::trim)
        .collect()
}
```

## Allocation Patterns

```rust
// Unnecessary allocation
let vec: Vec<i32> = vec![];  // Creates capacity
let vec: Vec<i32> = Vec::new();  // No allocation

// Pre-allocation
let mut vec = Vec::with_capacity(100);  // One allocation
for i in 0..100 {
    vec.push(i);  // No reallocation
}
```

## String Patterns

`clippy::single_char_pattern` is no longer in `clippy::perf`. It lives in `clippy::pedantic`, so do not rely on the perf group to flag `s.contains("x")`. A `char` pattern is still the clearer choice.

## See Also

- [lint-warn-complexity](./lint-warn-complexity.md) - Complexity warnings
- [mem-with-capacity](./mem-with-capacity.md) - Pre-allocation
- [perf-profile-first](./perf-profile-first.md) - Profile before optimizing
