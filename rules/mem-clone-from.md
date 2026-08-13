# mem-clone-from

> Use `clone_from()` to reuse allocations when repeatedly cloning

## Why It Matters

`Clone::clone_from` lets a type replace an existing value with a clone and may
reuse its storage. The trait's default implementation is equivalent to clone
plus assignment, so reuse is type/version-specific rather than guaranteed.
For a repeatedly replaced `String`, `Vec`, or application buffer, inspect the
concrete implementation and measure allocation behavior before preferring it.

## Bad

```rust
let mut buffer = String::with_capacity(1024);

for source in sources {
    buffer = source.clone();  // Drops old allocation, allocates new
    process(&buffer);
}

// Each iteration:
// 1. Drops buffer's 1024-byte allocation
// 2. Allocates new memory for source.clone()
// Allocator thrashing!
```

## Good

```rust
let mut buffer = String::with_capacity(1024);

for source in sources {
    buffer.clone_from(source);  // Reuses allocation if capacity sufficient
    process(&buffer);
}

// Current String implementations can reuse sufficient capacity. Treat this as
// an implementation optimization, not the generic Clone contract.
```

## Illustrative Custom Implementation

```rust
struct BufferText(String);

impl Clone for BufferText {
    fn clone(&self) -> Self {
        // Produces an independent String and ordinarily allocates for content.
        Self(String::from(self.0.as_str()))
    }
    
    fn clone_from(&mut self, source: &Self) {
        // Reuse existing capacity if possible
        self.0.clear();
        self.0.push_str(&source.0);
    }
}
```

## Types That Benefit

```rust
// String - reuses capacity
let mut s = String::with_capacity(100);
s.clone_from(&other_string);

// Vec<T> - reuses capacity
let mut v: Vec<u8> = Vec::with_capacity(1000);
v.clone_from(&other_vec);

// HashMap - measure the concrete implementation/version
let mut map = HashMap::with_capacity(100);
map.clone_from(&other_map);

// PathBuf - reuses capacity
let mut path = PathBuf::with_capacity(256);
path.clone_from(&other_path);
```

## Benchmarking the Difference

```rust
use criterion::{criterion_group, Criterion};
use std::hint::black_box;

fn bench_clone_patterns(c: &mut Criterion) {
    let source = "x".repeat(1000);
    
    c.bench_function("clone assignment", |b| {
        let mut buffer = String::new();
        b.iter(|| {
            buffer = black_box(&source).clone();
        });
    });
    
    c.bench_function("clone_from", |b| {
        let mut buffer = String::with_capacity(1000);
        b.iter(|| {
            buffer.clone_from(black_box(&source));
        });
    });
}
// Record allocation counts and benchmark uncertainty; do not assume a ratio.
```

## Custom Implementations

When implementing Clone for your types:

```rust
#[derive(Debug)]
struct Buffer {
    data: Vec<u8>,
    metadata: Metadata,
}

impl Clone for Buffer {
    fn clone(&self) -> Self {
        Buffer {
            data: self.data.clone(),
            metadata: self.metadata.clone(),
        }
    }
    
    // Optimize clone_from to reuse vec capacity
    fn clone_from(&mut self, source: &Self) {
        self.data.clone_from(&source.data);  // Reuses allocation
        self.metadata = source.metadata.clone();
    }
}
```

## When NOT Needed

```rust
// Single clone - no benefit
let copy = original.clone();  // Can't reuse, no prior allocation

// Small Copy types - no allocation anyway
let x: i32 = y;  // Not even Clone, just Copy

// Immutable context
fn process(data: &String) {
    // Can't use clone_from - would need &mut self
}
```

## See Also

- [mem-with-capacity](./mem-with-capacity.md) - Pre-allocating capacity
- [mem-reuse-collections](./mem-reuse-collections.md) - Reusing collection allocations
- [own-clone-explicit](./own-clone-explicit.md) - When Clone is appropriate
