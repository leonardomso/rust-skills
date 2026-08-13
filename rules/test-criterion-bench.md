# test-criterion-bench

> Use a statistical harness such as Criterion or Divan for repeatable benchmarks

## Why It Matters

Criterion provides statistically rigorous benchmarking with warmup, multiple iterations, outlier detection, and comparison between runs. Divan offers a smaller alternative with similar goals. Either is more reliable than a one-off `Instant::now()` measurement.

## Setup

```toml
# Cargo.toml
[dev-dependencies]
criterion = "0.5"

[[bench]]
name = "my_benchmark"
harness = false
```

## Basic Benchmark

```rust
// benches/my_benchmark.rs
use criterion::{criterion_group, criterion_main, Criterion};
use std::hint::black_box;

fn fibonacci(n: u64) -> u64 {
    match n {
        0 => 0,
        1 => 1,
        n => fibonacci(n - 1) + fibonacci(n - 2),
    }
}

fn bench_fibonacci(c: &mut Criterion) {
    c.bench_function("fib 20", |b| {
        b.iter(|| fibonacci(black_box(20)))
    });
}

criterion_group!(benches, bench_fibonacci);
criterion_main!(benches);
```

## black_box is Critical

```rust
// BAD: Compiler may optimize away the computation
b.iter(|| fibonacci(20));  // Result unused, might be eliminated

// GOOD: black_box prevents optimization
b.iter(|| fibonacci(black_box(20)));

// Also wrap the result if needed
b.iter(|| black_box(fibonacci(black_box(20))));
```

## Comparing Implementations

```rust
fn bench_comparison(c: &mut Criterion) {
    let mut group = c.benchmark_group("String concat");
    
    let data = "hello";
    
    group.bench_function("format!", |b| {
        b.iter(|| format!("{}{}", black_box(data), " world"))
    });
    
    group.bench_function("push_str", |b| {
        b.iter(|| {
            let mut s = String::from(black_box(data));
            s.push_str(" world");
            s
        })
    });
    
    group.bench_function("concat", |b| {
        b.iter(|| [black_box(data), " world"].concat())
    });
    
    group.finish();
}
```

## Parameterized Benchmarks

```rust
fn bench_vec_push(c: &mut Criterion) {
    let mut group = c.benchmark_group("Vec::push");
    
    for size in [100, 1000, 10000].iter() {
        group.bench_with_input(
            BenchmarkId::from_parameter(size),
            size,
            |b, &size| {
                b.iter(|| {
                    let mut v = Vec::new();
                    for i in 0..size {
                        v.push(black_box(i));
                    }
                    v
                });
            },
        );
    }
    
    group.finish();
}
```

## Throughput Measurement

```rust
use criterion::Throughput;

fn bench_parse(c: &mut Criterion) {
    let input = "a]ong string to parse...";
    
    let mut group = c.benchmark_group("Parser");
    group.throughput(Throughput::Bytes(input.len() as u64));
    
    group.bench_function("parse", |b| {
        b.iter(|| parse(black_box(input)))
    });
    
    group.finish();
}
```

## Wall Time vs CPU Time

Criterion measures elapsed wall time. That is the right user-visible measure
for single-threaded work, but it can hide the cost of parallel code: four
workers can finish in one second while consuming almost four CPU-seconds.
When a benchmark starts threads or runtime workers, report both:

- wall time and throughput, for latency and delivered work;
- process CPU time summed across threads, for compute cost.

Common Rust harnesses do not collect aggregate process CPU time
automatically. Measure it with the platform profiler or process accounting
used in production, and keep the worker count fixed between comparisons.

## Running Benchmarks

```bash
# Run all benchmarks
cargo bench

# Run specific benchmark
cargo bench -- fib

# Save baseline for comparison
cargo bench -- --save-baseline main

# Compare against baseline
cargo bench -- --baseline main
```

## Evidence from tokio

```rust
// https://github.com/tokio-rs/tokio/blob/master/benches/sync_mpsc.rs
use criterion::{criterion_group, criterion_main, Criterion};

fn send_data<T: Default, const SIZE: usize>(
    g: &mut BenchmarkGroup<WallTime>, 
    prefix: &str
) {
    let rt = rt();
    g.bench_function(format!("{prefix}_{SIZE}"), |b| {
        b.iter(|| {
            let (tx, mut rx) = mpsc::channel::<T>(SIZE);
            rt.block_on(tx.send(T::default())).unwrap();
            rt.block_on(rx.recv()).unwrap();
        })
    });
}
```

## See Also

- [perf-profile-first](perf-profile-first.md) - Profile before optimizing
- [perf-black-box-bench](perf-black-box-bench.md) - Use black_box in benchmarks
- [perf-batch-throughput](perf-batch-throughput.md) - compare delivered items with the CPU work used to produce them
