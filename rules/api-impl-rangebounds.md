# api-impl-rangebounds

> Accept `impl RangeBounds<T>` for range parameters instead of separate bounds or a concrete `Range`

## Why It Matters

Two loose `usize` parameters hide which end comes first and whether the end is inclusive. A concrete `Range<usize>` fixes the syntax to `a..b`, so callers cannot pass `..`, `a..`, or `..=b`. `impl RangeBounds<T>` accepts every range form the language has, which is what the standard library does for `Vec::drain` and `String::replace_range`.

## Bad

```rust
// Which is the end? Inclusive or exclusive?
pub fn select(items: &[u32], low: usize, high: usize) -> &[u32] {
    &items[low..high]
}

// Only `a..b` works; `2..` and `..=3` do not compile
pub fn select_range(items: &[u32], range: std::ops::Range<usize>) -> &[u32] {
    &items[range]
}
```

## Good

```rust
use std::ops::{Bound, RangeBounds};

pub fn select(items: &[u32], range: impl RangeBounds<usize>) -> &[u32] {
    let start = match range.start_bound() {
        Bound::Included(&s) => s,
        Bound::Excluded(&s) => s.saturating_add(1),
        Bound::Unbounded => 0,
    };
    let end = match range.end_bound() {
        Bound::Included(&e) => e.saturating_add(1),
        Bound::Excluded(&e) => e,
        Bound::Unbounded => items.len(),
    };
    let end = end.min(items.len());
    let start = start.min(end);
    &items[start..end]
}

fn demo(items: &[u32]) {
    let _ = select(items, 1..3);
    let _ = select(items, 2..);
    let _ = select(items, ..=4);
    let _ = select(items, ..);
}
```

## See Also

- [api-impl-asref](api-impl-asref.md) - Accept the most general borrowed input
- [api-impl-into](api-impl-into.md) - Accept flexible owned input
- [own-slice-over-vec](own-slice-over-vec.md) - Slices over owned containers
- Source: Microsoft Pragmatic Rust Guidelines, M-IMPL-RANGEBOUNDS
