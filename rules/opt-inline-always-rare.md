# opt-inline-always-rare

> Use `#[inline(always)]` sparingly—only for critical hot paths proven by profiling

## Why It Matters

`#[inline(always)]` is a strong request, not a language guarantee; recursion,
code-generation constraints, and other compiler decisions can still prevent
inlining. Overuse can increase binary size and instruction-cache pressure.
Reserve it for a measured hot path where representative benchmarks and
generated-code inspection show a benefit.

## Bad

```rust
// Annotating everything - trusting intuition over data
#[inline(always)]
pub fn get_name(&self) -> &str {
    &self.name
}

#[inline(always)]
pub fn calculate_tax(amount: f64) -> f64 {
    amount * 0.1
}

#[inline(always)]
fn helper(x: i32) -> i32 {
    x + 1
}

// Result: bloated binary, poor cache utilization
```

## Good

```rust
// Let compiler decide for most functions
pub fn get_name(&self) -> &str {
    &self.name
}

pub fn calculate_tax(amount: f64) -> f64 {
    amount * 0.1
}

// Use a strong request only when retained project evidence shows the ordinary
// #[inline] candidate leaves a material boundary on every supported target.
#[inline(always)]
fn decode_lane(value: u32, mask: u32) -> u32 {
    (value & mask).rotate_left(3)
}
```

## Candidates To Measure

```rust
// Tiny functions in a measured hot inner loop
#[inline(always)]
fn fast_hash(a: u64, b: u64) -> u64 {
    a.wrapping_mul(b).wrapping_add(a)
}

// A generic helper at a cross-crate optimization boundary
#[inline(always)]
fn swap<T>(a: &mut T, b: &mut T) {
    std::mem::swap(a, b);
}

// An iterator adapter whose call boundary remains in optimized output
#[inline(always)]
fn apply<T, F: Fn(T) -> T>(f: F, x: T) -> T {
    f(x)
}

// A small SIMD helper when the call boundary blocks vectorization
#[inline(always)]
fn add_simd(a: &[f32], b: &[f32], out: &mut [f32]) {
    // ...
}
```

## Inline Variants

```rust
// #[inline] - hint to inline, compiler may ignore
#[inline]
fn suggested_inline(x: i32) -> i32 { x + 1 }

// #[inline(always)] - strong request; still not a guarantee
#[inline(always)]
fn force_inline(x: i32) -> i32 { x + 1 }

// #[inline(never)] - prevent inlining (for profiling, code size)
#[inline(never)]
fn no_inline(x: i32) -> i32 { x + 1 }

// No annotation - compiler decides based on heuristics
fn compiler_decides(x: i32) -> i32 { x + 1 }
```

## Measuring Inline Impact

```rust
// Use criterion to benchmark
use criterion::{criterion_group, criterion_main, Criterion};

fn bench_with_inline(c: &mut Criterion) {
    c.bench_function("hot_path_inline", |b| {
        b.iter(|| hot_loop())
    });
}

// Compare binary sizes
// cargo bloat --release --crates

// Check if function was inlined
// cargo asm --rust my_crate::hot_function
```

## Generic Functions

```rust
// Measure cross-crate generic code before adding an inline hint.

// In library crate:
#[inline]  // Allow inlining in downstream crates
pub fn generic_function<T: Display>(x: T) {
    println!("{}", x);
}

// Generic functions are monomorphized for concrete types; the compiler can
// inline them without this attribute. The hint can still affect heuristics.
```

## See Also

- [opt-inline-small](./opt-inline-small.md) - Regular inline for small functions
- [opt-inline-never-cold](./opt-inline-never-cold.md) - Preventing inlining
- [perf-profile-first](./perf-profile-first.md) - Profile before optimizing
