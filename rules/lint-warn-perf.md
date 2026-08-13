# lint-warn-perf

> Enable `clippy::perf` as a review signal, then verify semantic and measured impact

## Why It Matters

Clippy's `perf` group detects source patterns that are often unnecessarily expensive while preserving behavior. A lint name is not benchmark evidence: allocator behavior, optimizer output, key sizes, surrounding I/O, readability, and API contracts determine product impact. Keep the group enabled, fix clear cases, and use narrow reasoned expectations when the suggested rewrite is wrong for the measured workload.

## Configuration

```toml
[workspace.lints.clippy]
perf = { level = "warn", priority = -1 }
```

Member crates opt into workspace policy:

```toml
[lints]
workspace = true
```

Promote selected high-confidence lints to `deny` after the existing workspace is clean. Pin the Rust toolchain because group membership and diagnostics can change between Clippy releases.

## Representative Findings

```rust
// A temporary Vec is unnecessary when an array supplies IntoIterator.
for value in vec![1, 2, 3] {
    consume(value);
}

for value in [1, 2, 3] {
    consume(value);
}
```

```rust
// Express the checked arithmetic contract directly.
fn add_capped(left: u32, right: u32) -> u32 {
    left.saturating_add(right)
}
```

```rust
// Copy a slice through its specialized contract.
fn append_copy(dst: &mut Vec<u8>, src: &[u8]) {
    dst.extend_from_slice(src);
}
```

The best rewrite depends on semantics. `saturating_add` is correct only when saturation is the domain policy; financial or security-sensitive arithmetic may need `checked_add` and a returned error.

## Allocation Claims Need Precision

```rust
let empty_a: Vec<i32> = vec![];
let empty_b: Vec<i32> = Vec::new();
```

Both empty vectors ordinarily start without allocating element storage; do not call one an allocation optimization. Likewise, `Vec::with_capacity(100)` requests capacity for at least 100 elements and can avoid growth during 100 pushes, but allocator rounding, zero-sized elements, fallible allocation, and later growth still matter.

```rust
let mut values = Vec::with_capacity(expected_count);
values.extend(source);
```

Reserve only from trusted, bounded estimates. An attacker-controlled `Content-Length` or size hint must not drive an unrestricted allocation.

## API And Ownership Trade-offs

A suggestion that removes `to_owned`, `clone`, boxing, or collection can change lifetimes, ownership, object safety, ordering, error timing, or memory retention. Review the public contract before accepting it. Passing `&str` to `impl Into<String>` still allocates when the callee converts; it merely moves the conversion. A `Box<dyn Trait>` may be required for heterogeneous storage or dynamic substitution even when static dispatch would be cheaper.

## Lint Expectations

```rust
#[expect(
    clippy::large_enum_variant,
    reason = "profile shows boxing the hot inline variant regresses latency"
)]
enum Message {
    Small(u8),
    Inline(Frame),
}
```

Use `#[expect]` rather than a broad `allow` so removal of the diagnostic becomes visible. The reason should cite a durable contract or benchmark evidence. Keep scope to the item/expression that needs the exception.

## Verification

- Run Clippy for all targets and the feature combinations the crate publishes; default features alone are not coverage.
- Compile tests, examples, benches, build scripts, and proc macros where applicable.
- Compare behavior before performance: overflow, Unicode, ordering, errors, and ownership must not change accidentally.
- Benchmark only hot-path changes on representative inputs and supported targets.
- Track binary size, allocation count/bytes, throughput, and tail latency according to the stated objective.
- Revisit expectations after toolchain and dependency upgrades.

## Common Non-Claims

- A `char` pattern is not universally faster than a one-character `&str` pattern.
- Iterator syntax does not guarantee vectorization, bounds-check removal, or no allocation.
- Removing an intermediate collection can increase repeated work or extend a borrow.
- Boxing does not automatically make a type faster; it adds allocation and indirection while possibly shrinking the containing value.
- `large_enum_variant` is a prompt to measure cardinality and access patterns, not an order to box.

## See Also

- [lint-static-verification](lint-static-verification.md) - cover targets and feature policy
- [perf-profile-first](./perf-profile-first.md) - require representative evidence
- [mem-with-capacity](./mem-with-capacity.md) - reserve only bounded known work
- [mem-box-large-variant](mem-box-large-variant.md) - measure enum representation trade-offs
