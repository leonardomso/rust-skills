# mem-compact-string

> Use compact string types for memory-constrained string storage

## Why It Matters

On common 64-bit targets, `String` is three machine words
(pointer, length, capacity). That representation and a separate allocation for
non-empty content can matter when a process retains millions of short strings.
Compact string crates use different inline or shared layouts, but their exact
size and inline capacity are crate-version and target details. Measure the
actual workload and lock the chosen dependency before making the representation
part of a long-lived type.

## Bad

```rust
struct User {
    id: u64,
    // Most usernames are short, but each String carries three words and
    // non-empty content ordinarily lives in a separate allocation.
    username: String,
    email: String,
}

// At this scale, measure metadata, allocation overhead, and content together.
```

## Good

```rust
use compact_str::CompactString;

struct User {
    id: u64,
    // CompactString can store sufficiently short strings inline.
    username: CompactString,
    email: CompactString,
}

// Verify the observed inline rate and total resident memory on the target.
```

## Compact String Libraries

### compact_str

```rust
use compact_str::CompactString;

// Short strings can use inline storage.
let small: CompactString = "hello".into();  // No heap allocation

// Automatic heap fallback for larger strings
let large: CompactString = "x".repeat(100).into();

// String-like API
let mut s = CompactString::new("hello");
s.push_str(" world");
assert_eq!(s.as_str(), "hello world");

// Format macro
use compact_str::format_compact;
let s = format_compact!("value: {}", 42);
```

### smartstring

```rust
use smartstring::{SmartString, LazyCompact};

// LazyCompact trades inline capacity against representation size.
let s: SmartString<LazyCompact> = "short string".into();

// Compact mode uses a different inline layout.
use smartstring::Compact;
let s: SmartString<Compact> = "hello".into();
```

### ecow (copy-on-write)

```rust
use ecow::EcoString;

// Heap-backed values can share their allocation on clone.
let s1: EcoString = "shared data".into();
let s2 = s1.clone();

// Mutation may detach shared heap-backed data.
let mut s3 = s1.clone();
s3.push_str(" modified");  // Now allocates
```

## Measure The Concrete Version

```rust
use std::mem::size_of;

// Record rather than assume these values for the supported target.
println!("String: {}", size_of::<String>());
println!("CompactString: {}", size_of::<compact_str::CompactString>());
println!(
    "SmartString: {}",
    size_of::<smartstring::SmartString<smartstring::LazyCompact>>(),
);
```

## Inline Capacity

Run an equivalent check for every candidate crate (including `EcoString`) in
the application that actually depends on it. Do not freeze a table from one
x86-64 release into a portability rule. Track object size, inline-hit rate,
clone/mutation behavior, and total allocated bytes on every supported target.
Empty `String` values need no content allocation, and shared/inline strings
have different clone costs.

## When to Use

```rust
// ✅ Good: Many short strings in memory
struct Dictionary {
    words: Vec<CompactString>,  // Millions of short words
}

// ✅ Good: Frequently cloned strings
struct Template {
    parts: Vec<EcoString>,  // Heap-backed parts may share on clone.
}

// ❌ Don't: Hot path string manipulation
fn transform(s: &str) -> String {
    // Standard String is optimized for manipulation
    s.to_uppercase()
}

// ❌ Don't: API boundaries (prefer &str or String for interop)
pub fn public_api(input: CompactString) { }  // Forces dependency
pub fn public_api(input: impl Into<String>) { }  // Better
```

## Cargo.toml

```toml
[dependencies]
compact_str = "0.9"
# or
smartstring = "1.0"
# or
ecow = "0.2"
```

## See Also

- [mem-boxed-slice](./mem-boxed-slice.md) - Box<str> for immutable strings
- [own-cow-conditional](./own-cow-conditional.md) - Cow<str> for borrow-or-own
- [mem-smallvec](./mem-smallvec.md) - Similar concept for Vec
