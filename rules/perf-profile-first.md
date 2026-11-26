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
    cloned.iter().map(|x| expensive_computation(x)).collect()
}

// Over-engineering rarely-called code
#[inline(always)]
fn rarely_called() {
    // This runs once at startup...
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
// 1. Profile first
// cargo flamegraph --bin myapp
// cargo instruments -t time --bin myapp (macOS)

// 2. Find the actual bottleneck
// Flamegraph shows expensive_computation takes 95% of time

// 3. Optimize the hot spot
fn process(data: &[Item]) -> Vec<Output> {
    // Clone is fine - only 1% of time
    let cloned: Vec<_> = data.iter().cloned().collect();
    
    // Focus optimization HERE
    cloned.par_iter()  // Parallelize the expensive part
        .map(|x| expensive_computation(x))
        .collect()
}

// Start simple; trust the compiler until a profile says otherwise
fn sum(data: &[i32]) -> i32 {
    data.iter().sum()
}
```

## Profiling Tools

### Flamegraphs (Recommended Start)

```bash
# Install
cargo install flamegraph

# Profile
cargo flamegraph --bin myapp -- <args>

# Opens flamegraph.svg showing call stacks by time
```

Rust 1.97 made the v0 symbol mangling scheme the default. Old profilers and debuggers may fail to demangle `_R...` symbols. Update them (and `rustfilt`) if names in a flamegraph look garbled.

### perf (Linux)

```bash
# Record
perf record -g cargo run --release

# Report
perf report

# Or generate flamegraph
perf script | inferno-collapse-perf | inferno-flamegraph > flamegraph.svg
```

### Instruments (macOS)

```bash
cargo install cargo-instruments
cargo instruments -t time --release   # time profiler
cargo instruments -t alloc --release  # allocations
```

### DHAT (Heap Profiling)

```bash
# In your code
#[global_allocator]
static ALLOC: dhat::Alloc = dhat::Alloc;

fn main() {
    let _profiler = dhat::Profiler::new_heap();
    // ... your code
}

# Run and get allocation report
cargo run --release
```

### criterion (Micro-benchmarks)

```rust
use criterion::{criterion_group, criterion_main, Criterion};
use std::hint::black_box;

fn bench_my_function(c: &mut Criterion) {
    c.bench_function("my_function", |b| {
        b.iter(|| my_function(black_box(input)))
    });
}

criterion_group!(benches, bench_my_function);
criterion_main!(benches);
```

## What to Look For

```
Flamegraph Reading:
├── Width = time spent
├── Height = call stack depth
└── Look for:
    ├── Wide bars (time hogs)
    ├── malloc/free (allocation heavy)
    ├── memcpy (copying data)
    └── Unexpected functions taking time
```

## Common Findings

```rust
// Finding: HashMap operations are slow
// Fix: Use FxHashMap or AHashMap for non-crypto hashing

// Finding: String allocation in hot loop
// Fix: Pre-allocate with capacity, use &str

// Finding: Clone in hot path
// Fix: Use references or Cow

// Finding: Bounds checks visible in profile
// Fix: Use iterators instead of indexing

// Finding: Lock contention
// Fix: Reduce critical section, use RwLock, or partition data
```

## Optimization Workflow

```
1. Write correct, simple code first
2. Write benchmarks for hot paths
3. Profile under realistic load
4. Identify actual bottlenecks (the top ~10% of time)
5. Optimize ONE thing
6. Measure again to verify the improvement
7. Repeat if still slow
```

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

## Evidence: Rust Performance Book

> "The biggest performance improvements often come from changes to algorithms or data structures, rather than low-level optimizations."

## See Also

- [opt-lto-release](opt-lto-release.md) - Enable LTO for release builds
- [test-criterion-bench](test-criterion-bench.md) - Use criterion for benchmarking
- [opt-inline-small](opt-inline-small.md) - Inline guidelines
- [mem-global-allocator](mem-global-allocator.md) - Benchmark an alternative global allocator
