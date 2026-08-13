# mem-shrink-to-fit

> Reclaim measured, long-lived collection slack after growth has finished; do not assume an exact capacity

## Why It Matters

`Vec`, `String`, and other growable collections may retain spare capacity, but
Rust does not specify their growth factor. `shrink_to_fit` asks the allocator to
reduce excess capacity; it does not guarantee `capacity() == len()`, and the
reallocation can cost more than the retained memory. Use it at a lifecycle
boundary only when the collection is long-lived, will not regrow soon, and
measurement shows meaningful slack.

## Bad

```rust
pub fn refill(buffer: &mut Vec<u8>, input: &[u8]) {
    buffer.clear();
    buffer.extend_from_slice(input);
    buffer.shrink_to_fit(); // churns the allocation before the next refill
}
```

## Good

```rust
pub fn freeze_index(mut offsets: Vec<u64>) -> Box<[u64]> {
    offsets.sort_unstable();
    offsets.dedup();
    offsets.into_boxed_slice()
}

pub fn finish_long_lived_buffer(buffer: &mut Vec<u8>) {
    let retained_bytes = buffer
        .capacity()
        .saturating_sub(buffer.len())
        .saturating_mul(std::mem::size_of::<u8>());

    if retained_bytes >= 1024 * 1024 {
        buffer.shrink_to_fit();
    }
}

fn main() {
    let frozen = freeze_index(vec![3, 1, 3]);
    assert_eq!(&*frozen, &[1, 3]);
}
```

The one-megabyte threshold is an example policy. Derive a real threshold from
object lifetime, allocator behavior, request concurrency, and memory SLOs.

## Key Points

- Reserve accurately before growth when the final size is predictable.
- Prefer `into_boxed_slice` when a growable collection becomes immutable.
- Do not shrink reusable scratch buffers, request-local values, or collections
  likely to regrow.
- Never assert an exact capacity after `with_capacity` or `shrink_to_fit`.
- Evaluate retained bytes, not only spare elements; element size matters.
- Measure allocator churn and resident memory under representative concurrency.

## See Also

- [mem-with-capacity](mem-with-capacity.md) - reserve from known input size
- [mem-boxed-slice](mem-boxed-slice.md) - freeze immutable sequences
- [mem-reuse-collections](mem-reuse-collections.md) - retain reusable allocation
- [perf-profile-first](perf-profile-first.md) - require evidence before trading CPU for memory
