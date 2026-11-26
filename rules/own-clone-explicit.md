# own-clone-explicit

> Use explicit `Clone` for types where copying has meaningful cost

## Why It Matters

Unlike `Copy` which is implicit and "free," `Clone` requires an explicit `.clone()` call, signaling that duplication has a cost. This makes heap allocations and deep copies visible in code, helping developers reason about performance. Types with heap data (`String`, `Vec`, `Box`) should implement `Clone` but not `Copy`.

## Bad

```rust
// `Copy` on a 4 KiB buffer: every assignment and by-value call silently
// copies 4096 bytes, and nothing at the call site shows it
#[derive(Clone, Copy)]
struct Frame {
    pixels: [u8; 4096],
}

fn checksum(frame: Frame) -> u32 {
    frame.pixels.iter().map(|&b| u32::from(b)).sum()
}

fn render(frame: Frame) {
    let a = checksum(frame); // 4 KiB copy
    let b = checksum(frame); // another 4 KiB copy
    let _ = (a, b);
}
```

## Good

```rust
// `Clone` only: duplication now needs a visible `.clone()`
#[derive(Clone)]
struct Frame {
    pixels: Box<[u8; 4096]>,
}

// Doesn't need ownership: borrow instead
fn checksum(frame: &Frame) -> u32 {
    frame.pixels.iter().map(|&b| u32::from(b)).sum()
}

// Needs ownership: take it by value
fn archive(frame: Frame) -> Vec<Frame> {
    vec![frame]
}

fn render(frame: Frame) -> Vec<Frame> {
    let _sum = checksum(&frame);      // no copy at all
    let kept = archive(frame.clone()); // explicit: "I know this allocates"
    let _ = checksum(&frame);         // still usable because we cloned
    kept
}

fn finish(frame: Frame) -> Vec<Frame> {
    archive(frame) // caller is done with it: just move, no clone
}
```

At a call site, the cheapest correct option wins: borrow if the callee only reads, move if the caller no longer needs the value, and write `.clone()` only when both sides need their own copy.

## Custom Clone Implementation

For types with mixed cheap/expensive fields, implement `Clone` manually:

```rust
#[derive(Debug)]
struct Document {
    id: u64,              // Cheap to copy
    content: String,      // Expensive to clone
    metadata: Metadata,   // Moderate cost
}

impl Clone for Document {
    fn clone(&self) -> Self {
        Self {
            id: self.id,
            content: self.content.clone(),
            metadata: self.metadata.clone(),
        }
    }
    
    // Optimization: reuse existing allocations
    fn clone_from(&mut self, source: &Self) {
        self.id = source.id;
        self.content.clone_from(&source.content); // Reuses capacity
        self.metadata.clone_from(&source.metadata);
    }
}
```

## clone_from Optimization

`clone_from` can reuse existing allocations:

```rust
let mut buffer = String::with_capacity(1000);

// Bad: drops old allocation, creates new one
buffer = source.clone();

// Good: reuses existing capacity if sufficient
buffer.clone_from(&source);
```

## Derive vs Manual Clone

```rust
// Derive when all fields need cloning
#[derive(Clone)]
struct Simple {
    data: Vec<u8>,
    name: String,
}

// Manual when you need special behavior
struct CachedValue {
    value: i32,
    cache: RefCell<Option<ExpensiveComputation>>,
}

impl Clone for CachedValue {
    fn clone(&self) -> Self {
        Self {
            value: self.value,
            cache: RefCell::new(None), // Don't clone cache, let it rebuild
        }
    }
}
```

## When to Avoid Clone

```rust
// Instead of cloning, consider:

// 1. References
fn process(data: &MyType) { } // Borrow instead of clone

// 2. Cow for conditional cloning
fn process(data: Cow<'_, str>) { } // Clone only if mutation needed

// 3. Arc for shared ownership
let shared = Arc::new(expensive_data);
let handle = shared.clone(); // Cheap: just increments counter

// 4. Passing by value when caller is done with it
fn consume(data: MyType) { } // Caller moves, no clone
```

## See Also

- [own-copy-small](./own-copy-small.md) - When implicit Copy is appropriate
- [own-cow-conditional](./own-cow-conditional.md) - Avoiding clones with Cow
- [mem-clone-from](./mem-clone-from.md) - Optimizing repeated clones
