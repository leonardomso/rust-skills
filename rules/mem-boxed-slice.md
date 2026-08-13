# mem-boxed-slice

> Use `Box<[T]>`, `Arc<[T]>`, or `Arc<str>` for internal fixed-size heap data

## Why It Matters

`Vec<T>` tracks pointer, length, and capacity. A boxed slice has no growth
capacity and is represented as an owned slice pointer. On common 64-bit targets
that often makes the handle one machine word smaller, but Rust does not promise
those exact sizes as a stable ABI. More importantly, the type communicates
"fixed after construction." `into_boxed_slice` and `into_boxed_str` already
discard spare capacity, so a preceding `shrink_to_fit()` is redundant. Use the
pattern for measured, high-cardinality internal storage; keep public, growable,
or rarely created collections as `Vec` or `String`.

## Bad

```rust
struct Document {
    // Vec signals "might grow" but we never push after creation
    paragraphs: Vec<Paragraph>,  // carries growth capacity
}

fn load_document(data: &[u8]) -> Document {
    let paragraphs: Vec<Paragraph> = parse_paragraphs(data);
    // paragraphs has capacity >= len, wasting the capacity field
    Document { paragraphs }
}
```

## Good

```rust
struct Document {
    // Private storage signals fixed size; callers receive a slice.
    paragraphs: Box<[Paragraph]>,
}

impl Document {
    pub fn paragraphs(&self) -> &[Paragraph] {
        &self.paragraphs
    }
}

fn load_document(data: &[u8]) -> Document {
    let paragraphs: Vec<Paragraph> = parse_paragraphs(data);
    Document { 
        paragraphs: paragraphs.into_boxed_slice()  // Shrinks + converts
    }
}
```

## Memory Layout

```rust
use std::mem::size_of;

// Measure the deployment target; do not make these sizes a wire or ABI contract.
#[cfg(target_pointer_width = "64")]
assert!(size_of::<Box<[u8]>>() < size_of::<Vec<u8>>());
```

## Conversion Patterns

```rust
// Vec to Box<[T]>
let vec: Vec<i32> = vec![1, 2, 3, 4, 5];
let boxed: Box<[i32]> = vec.into_boxed_slice();

// Box<[T]> back to Vec (if you need to grow)
let vec_again: Vec<i32> = boxed.into_vec();

// From iterator
let boxed: Box<[i32]> = (0..100).collect::<Vec<_>>().into_boxed_slice();

// into_boxed_slice already sheds spare capacity — no shrink_to_fit first
let mut vec = Vec::with_capacity(1000);
vec.extend(0..10);
let boxed = vec.into_boxed_slice();
// Shared owned bytes: same fat pointer, plus a refcount
let shared: std::sync::Arc<[i32]> = vec![1, 2, 3].into();
let _ = shared;
```

## When to Use What

| Type | Use When |
|------|----------|
| `Vec<T>` | Collection may grow/shrink |
| `Box<[T]>` | Fixed-size, heap-allocated, many instances |
| `[T; N]` | Fixed-size, stack-allocated, size known at compile time |
| `&[T]` | Borrowed view, don't need ownership |
| `Arc<[T]>` | Fixed-size, shared by several owners, many internal instances |
| `Arc<str>` | Shared immutable text; callers still see `&str` |
| `Box<str>` | Owned immutable text, single owner |

## Box<str> and Arc<str> for Immutable Strings

Same principle applies to strings. Prefer these in private fields; keep the public surface on `&str`.

```rust
use std::mem::size_of;

#[cfg(target_pointer_width = "64")]
assert!(size_of::<Box<str>>() < size_of::<String>());

// For immutable strings
struct Name {
    value: Box<str>,  // Carries no spare-capacity field
}

impl Name {
    fn new(s: &str) -> Self {
        Name { value: s.into() }  // &str -> Box<str>
    }
}

// Or from String
let s = String::from("hello");
let boxed: Box<str> = s.into_boxed_str();
// Shared immutable text: still presented to callers as `&str`
use std::sync::Arc;
struct SharedName {
    value: Arc<str>,
}
impl SharedName {
    fn new(s: &str) -> Self {
        SharedName { value: Arc::from(s) }
    }
    fn as_str(&self) -> &str {
        &self.value
    }
}
```

## Real-World Example

```rust
// Cache with millions of entries
struct Cache {
    // A measured handle-size reduction can add up at high cardinality
    entries: HashMap<Key, Box<[u8]>>,
}

impl Cache {
    fn insert(&mut self, key: Key, data: Vec<u8>) {
        // Convert to boxed slice for storage
        self.entries.insert(key, data.into_boxed_slice());
    }
    
    fn get(&self, key: &Key) -> Option<&[u8]> {
        // Returns regular slice reference
        self.entries.get(key).map(|b| b.as_ref())
    }
}
```

## See Also

- [mem-with-capacity](./mem-with-capacity.md) - Pre-allocating when size is known
- [own-slice-over-vec](./own-slice-over-vec.md) - Using slices in function parameters
- [mem-compact-string](./mem-compact-string.md) - Compact string alternatives
- [mem-shrink-to-fit](./mem-shrink-to-fit.md) - Shrink a long-lived `Vec`; boxed conversion already does this
- [own-arc-shared](./own-arc-shared.md) - `Arc<[T]>` / `Arc<str>` when several owners share the bytes
