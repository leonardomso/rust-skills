# perf-profile-first

> Profile under a realistic workload, then optimize only the measured hot spot

## Why It Matters

Intuition about performance is often wrong. The code you think is slow frequently isn't, while actual bottlenecks hide in unexpected places. Profiling shows you exactly where time is spent, preventing wasted effort on optimizations that don't matter.

## Bad

```rust
// Optimizing without measuring
fn process(data: &[Item]) -> Vec<Output> {
    // "I bet this clone is slow..."
    let cloned: Vec<_> = data.iter().cloned().collect();

    // Actually, 99% of time is spent here:
    cloned.iter().map(expensive_computation).collect()
}

// Unsafe "for speed" with no evidence; iterators already elide bounds checks
fn sum(data: &[i32]) -> i32 {
    let mut sum = 0;
    for i in 0..data.len() {
        sum += unsafe { *data.get_unchecked(i) };
    }
    sum
}
```

## Good

```rust
use rayon::prelude::*;

#[derive(Clone)]
struct Item(u64);
struct Output(u64);

fn expensive_computation(item: &Item) -> Output {
    Output((0..item.0).sum())
}

// 1. Profile: `cargo flamegraph --bin myapp`
// 2. The flamegraph shows expensive_computation takes 95% of the time
// 3. Optimize only that part
fn process(data: &[Item]) -> Vec<Output> {
    // The clone is 1% of the time: leave it alone
    let cloned: Vec<_> = data.iter().cloned().collect();
    cloned.par_iter().map(expensive_computation).collect()
}

// Start simple; trust the compiler until a profile says otherwise
fn sum(data: &[i32]) -> i32 {
    data.iter().sum()
}
```

## Profiling Tools

```bash
# Flamegraph (cross-platform start): writes flamegraph.svg
cargo install flamegraph
cargo flamegraph --bin myapp -- <args>

# Linux perf
perf record -g cargo run --release
perf report

# macOS Instruments
cargo install cargo-instruments
cargo instruments -t time --release    # CPU
cargo instruments -t alloc --release   # allocations
```

Use DHAT (`dhat::Profiler::new_heap()` with `dhat::Alloc` as the global allocator) for heap profiles, and [test-criterion-bench](test-criterion-bench.md) for micro-benchmarks.

Rust 1.97 made the v0 symbol mangling scheme the default. Old profilers and debuggers may fail to demangle `_R...` symbols. Update them (and `rustfilt`) if names in a flamegraph look garbled.

In a flamegraph, width is time spent. Look for wide bars, `malloc`/`free` (allocation heavy), `memcpy` (copying), and functions you did not expect.

## Common Findings

| Finding | Fix |
|---------|-----|
| Slow `HashMap` operations | Non-crypto hasher, see [perf-ahash](perf-ahash.md) |
| String allocation in a hot loop | Pre-allocate with capacity, use `&str` |
| `clone` in a hot path | Use references or `Cow` |
| Bounds checks visible in profile | Use iterators, see [perf-iter-over-index](perf-iter-over-index.md) |
| Lock contention | Shrink the critical section, use `RwLock`, or partition data |

## Optimization Workflow

1. Write correct, simple code first.
2. Write benchmarks for hot paths.
3. Profile under realistic load.
4. Find the real bottleneck (the top ~10% of time).
5. Optimize one thing.
6. Measure again to verify the gain.
7. Repeat if still slow.

Keep the optimization only if the numbers justify it, and record them next to the code:

```rust
/// Lookup table for fast character classification.
///
/// # Performance
///
/// Benchmarked with criterion (benches/char_class.rs):
/// - Table lookup: 2.3ns/op
/// - Match statement: 8.7ns/op
///
/// Justified for the parser hot path (called 10M+ times).
static CHAR_CLASS: [u8; 256] = [0; 256];
```

## Common Premature Optimizations

| Premature | Reality |
|-----------|---------|
| `#[inline(always)]` everywhere | Compiler usually knows better |
| `unsafe` for bounds check removal | Iterators do this safely |
| Custom allocator | Default is usually fine; benchmark first |
| Object pooling | Allocator is fast enough |
| Manual SIMD | Auto-vectorization often works |

The Rust Performance Book: "The biggest performance improvements often come from changes to algorithms or data structures, rather than low-level optimizations."

## See Also

- [opt-lto-release](opt-lto-release.md) - Enable LTO for release builds
- [test-criterion-bench](test-criterion-bench.md) - Use criterion for benchmarking
- [opt-inline-small](opt-inline-small.md) - Inline guidelines
- [mem-global-allocator](mem-global-allocator.md) - Benchmark an alternative global allocator
