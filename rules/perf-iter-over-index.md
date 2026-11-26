# perf-iter-over-index

> Iterate with `iter()`, `iter_mut()`, `zip` and adapters instead of indexing in a `0..len` loop

## Why It Matters

Iterators are the idiomatic way to traverse collections in Rust. They remove per-access bounds checks, let the compiler auto-vectorize, and rule out off-by-one errors. Manual indexing (`for i in 0..len`) often blocks these optimizations.

## Bad

```rust
// Manual indexing - bounds checked every iteration
fn sum_squares(data: &[i32]) -> i64 {
    let mut sum = 0i64;
    for i in 0..data.len() {
        sum += (data[i] as i64) * (data[i] as i64);
    }
    sum
}

// Index-based iteration with multiple collections
fn dot_product(a: &[f64], b: &[f64]) -> f64 {
    let mut sum = 0.0;
    for i in 0..a.len().min(b.len()) {
        sum += a[i] * b[i];
    }
    sum
}

// Mutating with indices
fn double_values(data: &mut [i32]) {
    for i in 0..data.len() {
        data[i] *= 2;
    }
}
```

## Good

```rust
// Iterator - bounds checks eliminated, SIMD-friendly
fn sum_squares(data: &[i32]) -> i64 {
    data.iter()
        .map(|&x| (x as i64) * (x as i64))
        .sum()
}

// Zip - handles length mismatch automatically
fn dot_product(a: &[f64], b: &[f64]) -> f64 {
    a.iter()
        .zip(b.iter())
        .map(|(&x, &y)| x * y)
        .sum()
}

// Mutable iteration
fn double_values(data: &mut [i32]) {
    for x in data.iter_mut() {
        *x *= 2;
    }
}
```

## Common Conversions

| Index Pattern | Iterator Pattern |
|---------------|------------------|
| `for i in 0..v.len() { v[i] }` | `for x in &v` |
| `for i in 0..v.len() { v[i] *= 2 }` | `for x in &mut v { *x *= 2 }` |
| `for i in 0..a.len() { a[i] + b[i] }` | `a.iter().zip(&b)` |
| `v[0]` | `v.first()` |
| `v[v.len() - 1]` | `v.last()` |

## When Indexing Is Needed

Use an index when you need it as a value or the access is not sequential. Prefer `enumerate()` when you only need the index alongside each item.

```rust
// Need the index for output or processing
fn print_all(data: &[i32]) {
    for (i, value) in data.iter().enumerate() {
        println!("Index {}: {}", i, value);
    }
}

// Non-sequential access
fn interleave(data: &mut [i32]) {
    let mid = data.len() / 2;
    for i in 0..mid {
        data.swap(i * 2, mid + i);
    }
}
```

## Performance Comparison

| Pattern | Bounds Checks | SIMD Potential |
|---------|---------------|----------------|
| `for i in 0..len` | Every access | Limited |
| `for &x in slice` / `.iter().enumerate()` | None | High / Medium |
| `get_unchecked` | None (unsafe) | High, but needs `unsafe` |

## Iterator Advantages

```rust
// Chaining operations - single pass
let result: Vec<_> = data.iter()
    .filter(|x| **x > 0)
    .map(|x| x * 2)
    .collect();

// Early termination optimized
let found = data.iter().any(|&x| x == target);

// Parallel iteration (with rayon)
use rayon::prelude::*;
let sum: i64 = data.par_iter().map(|&x| x as i64).sum();
```

## See Also

- [perf-iter-lazy](./perf-iter-lazy.md) - Keep iterators lazy
- [opt-bounds-check](./opt-bounds-check.md) - Bounds check elimination
- [conc-rayon-par-iter](./conc-rayon-par-iter.md) - Parallelize data-parallel loops
