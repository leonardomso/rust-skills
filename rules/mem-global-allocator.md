# mem-global-allocator

> For allocation-heavy applications, try a different global allocator and keep it only if benchmarks improve

## Why It Matters

The default system allocator is a general-purpose choice. Applications that allocate and free many small objects across threads can run noticeably faster, or use less memory, with an allocator such as mimalloc or jemalloc. The gain depends on the workload and platform, and some programs see none, so treat it as an experiment. Only a binary should choose the global allocator; a library must not.

## Bad

```rust
// A library crate forcing an allocator on everyone who depends on it
#[global_allocator]
static GLOBAL: std::alloc::System = std::alloc::System;
```

## Good

```toml
# Cargo.toml of the application
[dependencies]
mimalloc = "0.1"
```

```rust,ignore
// main.rs of the application
use mimalloc::MiMalloc;

#[global_allocator]
static GLOBAL: MiMalloc = MiMalloc;

fn main() {
    // application code
}
```

## How to Decide

1. Benchmark a realistic workload with the default allocator and record throughput, latency, and peak memory.
2. Switch the allocator (the change is a few lines) and run the same benchmark.
3. Keep the new allocator only if the numbers improve on the platforms you ship. Re-check after major dependency or workload changes.

## See Also

- [perf-profile-first](perf-profile-first.md) - Measure before and after
- [mem-allocator-api](mem-allocator-api.md) - Per-collection allocators instead of a global one
- [mem-arena-allocator](mem-arena-allocator.md) - Arena allocation for batch workloads
- [perf-release-profile](perf-release-profile.md) - Release profile settings
- Source: Microsoft Pragmatic Rust Guidelines, M-MIMALLOC-APPS (adopted as an optional, measure-first suggestion)
