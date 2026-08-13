# mem-thinvec

> Consider `ThinVec<T>` only after measuring many sparse collection handles

## Why It Matters

`ThinVec` moves length and capacity metadata behind its pointer, reducing the
inline handle on common targets at the cost of indirection and a third-party
dependency. Exact size and niche behavior are implementation- and
target-specific. It can reduce resident memory when a program holds millions of
mostly empty collection fields; it can also regress hot access and complicate
the dependency surface. Measure the actual type, target, allocator, and
workload before changing a `Vec`.

## Bad

```rust
struct TreeNode {
    value: i32,
    // The full Vec handle is present even for leaves
    children: Vec<TreeNode>,
}

// Or using Option<Vec<T>>
struct SparseData {
    // Measure Option<Vec> layout on the deployment target
    tags: Option<Vec<String>>,
    metadata: Option<Vec<Metadata>>,
    // Two usually-empty collection handles
}
```

## Good

```rust
use thin_vec::ThinVec;

struct TreeNode {
    value: i32,
    // ThinVec stores collection metadata out of line
    children: ThinVec<TreeNode>,
}

struct SparseData {
    // Smaller inline handles on the measured target/version
    tags: ThinVec<String>,
    metadata: ThinVec<Metadata>,
    // Confirm the aggregate layout with size_of
}
```

## Memory Layout

```rust
use std::mem::size_of;

// Illustrative checks for the measured deployment target, not ABI guarantees
#[cfg(target_pointer_width = "64")]
assert_eq!(size_of::<Vec<u8>>(), 24);
#[cfg(target_pointer_width = "64")]
assert_eq!(size_of::<Option<Vec<u8>>>(), 24);

use thin_vec::ThinVec;
#[cfg(target_pointer_width = "64")]
assert_eq!(size_of::<ThinVec<u8>>(), 8);
#[cfg(target_pointer_width = "64")]
assert_eq!(size_of::<Option<ThinVec<u8>>>(), 8);
```

## ThinVec vs Vec

| Feature | `Vec<T>` | `ThinVec<T>` |
|---------|----------|--------------|
| Inline handle size | Larger in current 64-bit implementations | Smaller; header is out of line |
| Empty collection | Inline metadata remains | Uses the crate's empty representation |
| `Option` niche | Measure | Measure |
| Cache locality | Better (len/cap on stack) | Worse (len/cap on heap) |
| Iteration speed | Measure | Measure |
| API compatibility | Full | Vec-like |

## When to Use ThinVec

```rust
// ✅ Good: Many instances, often empty
struct SparseGraph {
    nodes: Vec<Node>,
    // Most edges lists are empty or small
    edges: Vec<ThinVec<EdgeId>>,  // Measure aggregate savings
}

// ✅ Good: Nullable collection field
struct Document {
    content: String,
    attachments: ThinVec<Attachment>,  // Often empty
}

// ❌ Avoid: Hot loops, performance-critical iteration
fn process_hot_path(data: &ThinVec<Item>) {
    // Header access differs; benchmark a hot iteration path
    for item in data {
        process(item);
    }
}

// ❌ Avoid: Few instances
fn main() {
    let single_vec: ThinVec<i32> = ThinVec::new();
    // One handle rarely justifies an added dependency
}
```

## API Compatibility

```rust
use thin_vec::{ThinVec, thin_vec};

// Constructor macro
let v: ThinVec<i32> = thin_vec![1, 2, 3];

// Familiar Vec-like API
let mut v = ThinVec::new();
v.push(1);
v.push(2);
v.extend([3, 4, 5]);
v.pop();

// Iteration
for item in &v {
    println!("{}", item);
}

// Slicing
let slice: &[i32] = &v[..];

// Conversion
let vec: Vec<i32> = v.into();
let thin: ThinVec<i32> = vec.into();
```

## Cargo.toml

```toml
[dependencies]
thin-vec = "0.2"
```

## See Also

- [mem-smallvec](./mem-smallvec.md) - Stack-allocated small vecs
- [mem-boxed-slice](./mem-boxed-slice.md) - Fixed-size heap slices
- [mem-with-capacity](./mem-with-capacity.md) - Pre-allocation strategies
