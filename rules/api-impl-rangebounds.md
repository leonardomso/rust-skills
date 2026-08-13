# api-impl-rangebounds

> Accept `impl RangeBounds<T>` for range parameters instead of a pair of endpoints or a concrete `Range`

## Why It Matters

A function that takes `(low, high)` or only `Range<usize>` cannot express "from here to the end" or "everything" without inventing sentinels. `RangeBounds` is the standard-library trait behind `1..3`, `1..`, `..3`, and `..`. Treat it like `AsRef` and `Read`: one parameter accepts every range syntax the caller already knows.

## Bad

```rust
pub fn slice_span(low: usize, high: usize) -> (usize, usize) {
    (low, high)
}

pub fn slice_pair(range: (usize, usize)) -> (usize, usize) {
    range
}
```

## Good

```rust
use std::ops::{Bound, Range, RangeBounds};

pub fn slice_half_open(range: Range<usize>) -> Range<usize> {
    range
}

pub fn index_in(range: impl RangeBounds<usize>, index: usize) -> bool {
    range.contains(&index)
}

fn describe(range: impl RangeBounds<usize>) -> (Bound<usize>, Bound<usize>) {
    let start = match range.start_bound() {
        Bound::Included(n) => Bound::Included(*n),
        Bound::Excluded(n) => Bound::Excluded(*n),
        Bound::Unbounded => Bound::Unbounded,
    };
    let end = match range.end_bound() {
        Bound::Included(n) => Bound::Included(*n),
        Bound::Excluded(n) => Bound::Excluded(*n),
        Bound::Unbounded => Bound::Unbounded,
    };
    (start, end)
}

fn main() {
    let _ = slice_half_open(1..3);
    assert!(index_in(1.., 4));
    assert!(index_in(.., 0));
    let _ = describe(1..3);
}
```

## See Also

- [api-impl-asref](api-impl-asref.md) - the same flexibility for borrowed string, path, and byte inputs
- [api-impl-io](api-impl-io.md) - accept `Read`/`Write` instead of a concrete file
- [api-impl-into](api-impl-into.md) - accept `impl Into<T>` when you need ownership
