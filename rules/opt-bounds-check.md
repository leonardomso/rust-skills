# opt-bounds-check

> Prefer safe traversal that exposes bounds; verify optimized hot loops before considering unchecked access

## Why It Matters

Array and slice indexing must panic when an index is out of bounds. In a
measured hot loop, a residual check can matter, but source syntax does not say
which checks LLVM will remove. Iterators, slice patterns, `windows`,
`chunks_exact`, and `split_at` express the valid range directly and often
compile to the same loop as unchecked access. Preserve behavior first, inspect
optimized code second, and use unsafe access only when a benchmark and the
generated code prove a remaining check matters.

## Bad

```rust
fn sum_products(a: &[f64], b: &[f64]) -> f64 {
    let mut sum = 0.0;
    for i in 0..a.len() {
        // Panics part-way through when b is shorter.
        sum += a[i] * b[i];
    }
    sum
}

fn apply_filter(data: &mut [u8]) {
    // Underflows when data is empty and mixes old and newly written samples.
    for i in 1..data.len() - 1 {
        data[i] = (data[i - 1] + data[i] + data[i + 1]) / 3;
    }
}
```

## Good

```rust
fn sum_products(a: &[f64], b: &[f64]) -> f64 {
    assert_eq!(a.len(), b.len(), "vectors must have equal length");
    a.iter().zip(b.iter()).map(|(x, y)| x * y).sum()
}

fn smooth_into(input: &[u8], output: &mut [u8]) {
    assert_eq!(output.len(), input.len().saturating_sub(2));

    for (dst, window) in output.iter_mut().zip(input.windows(3)) {
        let sum = u16::from(window[0])
            + u16::from(window[1])
            + u16::from(window[2]);
        *dst = u8::try_from(sum / 3).expect("average of three u8 values fits");
    }
}
```

The length assertion preserves the original dot-product contract instead of
silently truncating to the shorter input. The filter reads an immutable input,
writes a separate output, handles short input without subtraction overflow,
and widens before addition.

## Iterator Patterns

```rust
// These make valid ranges explicit. Check optimized code before claiming that
// a particular compiler version removed every bounds check.

// zip - parallel iteration
for (a, b) in xs.iter().zip(ys.iter()) { ... }

// enumerate - index + value  
for (i, x) in data.iter().enumerate() { ... }

// windows - sliding window
for window in data.windows(3) { ... }

// chunks - fixed-size groups
for chunk in data.chunks(4) { ... }
for chunk in data.chunks_exact(4) { ... }  // Every yielded chunk has length 4

// split_at - divide slice
let (left, right) = data.split_at(mid);
```

## Split for Parallel Access

```rust
fn parallel_sum(data: &[i32]) -> i32 {
    // Split into independent chunks
    let (left, right) = data.split_at(data.len() / 2);
    
    // Process independent slices without coordinating indices manually.
    let sum_left: i32 = left.iter().sum();
    let sum_right: i32 = right.iter().sum();
    
    sum_left + sum_right
}
```

## Unchecked Access Is a Last Step

Do not translate a checked loop mechanically to `get_unchecked`. Index
arithmetic can overflow, related slice lengths can drift, and a future edit can
invalidate an old `SAFETY` proof. First try a safe traversal and inspect the
optimized function. If a residual check is measured and material, isolate the
unchecked operation behind an `unsafe fn` whose `# Safety` contract covers
lengths and overflow, keep a checked implementation as the reference, and test
both implementations for identical output.

## Slice Patterns

```rust
fn process_header(data: &[u8]) -> Option<Header> {
    // Slice pattern - single length check, no per-field checks
    let [a, b, c, d, rest @ ..] = data else {
        return None;
    };
    
    Some(Header {
        magic: *a,
        version: *b,
        flags: u16::from_le_bytes([*c, *d]),
        payload: rest,
    })
}
```

## Verify Bounds Check Elimination

```bash
# Check generated assembly
cargo asm --release my_crate::hot_function

# Compare the complete hot loop. A compare instruction may be a loop bound,
# data comparison, or a bounds check; its mnemonic alone is not proof.
```

## When to Accept Bounds Checks

```rust
// Random access patterns need validation somewhere.
fn random_lookup(data: &[u8], indices: &[usize]) -> Vec<u8> {
    indices.iter()
        .filter_map(|&i| data.get(i).copied())  // Checked, but necessary
        .collect()
}

// Infrequent access - overhead negligible
fn get_config(&self, key: &str) -> Option<&Value> {
    self.config.get(key)  // Fine, not hot path
}
```

## See Also

- [opt-simd-portable](./opt-simd-portable.md) - vectorize only after measurement
- [opt-cache-friendly](./opt-cache-friendly.md) - Cache-efficient patterns
- [perf-profile-first](./perf-profile-first.md) - Identify actual hot paths
