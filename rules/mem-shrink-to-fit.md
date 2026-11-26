# mem-shrink-to-fit

> Call `shrink_to_fit()` on large, long-lived collections that were built by pushing

## Why It Matters

`Vec` and `String` grow geometrically, so after many pushes the capacity can be close to twice the length. For a short-lived buffer that does not matter. For a big collection that lives for the whole program, such as a loaded index or a lookup table, the unused half is wasted memory. When you cannot reserve the exact size up front, shrink once after building.

## Bad

```rust
fn load_index(lines: impl Iterator<Item = String>) -> Vec<String> {
    let mut index = Vec::new();
    for line in lines {
        index.push(line);
    }
    // Capacity may be up to ~2x the length for the rest of the program
    index
}
```

## Good

```rust
fn load_index(lines: impl Iterator<Item = String>) -> Vec<String> {
    let mut index = Vec::new();
    for line in lines {
        index.push(line);
    }
    // Release the spare capacity once, after the last push
    index.shrink_to_fit();
    index
}
```

## Notes

- If the final size is known, prefer `Vec::with_capacity` and skip the shrink.
- If the collection will never grow again, `into_boxed_slice()` already trims capacity. See [mem-boxed-slice](mem-boxed-slice.md).
- `shrink_to_fit` may reallocate and copy, so do it once at the end, not in a loop.

## See Also

- [mem-with-capacity](mem-with-capacity.md) - Reserve the right size up front
- [mem-boxed-slice](mem-boxed-slice.md) - `Box<[T]>` for fixed-size data
- [mem-reuse-collections](mem-reuse-collections.md) - Keep capacity for buffers that are reused
- Source: Microsoft Pragmatic Rust Guidelines, M-SHRINK-TO-FIT
