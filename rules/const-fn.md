# const-fn

> Make functions `const fn` when they can run at compile time

## Why It Matters

A `const fn` can be called in const contexts—array lengths, `const`/`static`
initializers, and const-generic arguments—as well as at runtime. Marking a
function `const` expands its public contract: calls required by a const context
are evaluated during compilation, while ordinary calls retain normal runtime
semantics and optimization. Const-evaluable operations evolve by Rust release,
so use only capabilities supported by the crate's MSRV.

## Bad

```rust
// not const — cannot use result as an array length or const initializer
fn header_len() -> usize {
    4
}

fn magic_mask() -> u32 {
    0xFF00_FF00
}

fn make_buf() -> [u8; 8] {
    // A non-const call is not allowed in an array length.
    [0u8; header_len()]  // error: `header_len` is not a `const fn`
}
```

## Good

```rust
const fn header_len() -> usize {
    4
}

const fn magic_mask() -> u32 {
    0xFF00_FF00
}

// usable as an array length — evaluated at compile time
let buf = [0u8; header_len()];

// usable in a const initializer
const MASK: u32 = magic_mask();

// usable in a static
static HEADER: [u8; header_len()] = [0u8; header_len()];

// const fn with logic — still fine on stable
const fn align_up(n: usize, align: usize) -> Option<usize> {
    if !align.is_power_of_two() {
        return None;
    }
    let mask = align - 1;
    match n.checked_add(mask) {
        Some(sum) => Some(sum & !mask),
        None => None,
    }
}

const ALIGNED: Option<usize> = align_up(13, 8); // Some(16)
```

## Notes

Adding `const` is generally backwards-compatible. Removing it later can break
callers that use the function in const contexts, so treat const-evaluability as
part of a public API's compatibility surface. Add it when the supported MSRV
can express the durable implementation; do not promise it speculatively and
then remove it when a non-const operation becomes convenient.

## See Also

- [const-block](const-block.md) - force compile-time evaluation and assertions inline
- [const-generics](const-generics.md) - parameterize types and functions over const values
- [opt-inline-small](opt-inline-small.md) - inline small hot functions
