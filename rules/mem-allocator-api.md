# mem-allocator-api

> Use the stable `Allocator` trait with `Vec::new_in` and `Box::new_in` to control where a collection allocates

## Why It Matters

Since Rust 1.100, `std::alloc::Allocator`, `Global`, `System`, and the `_in` constructors on `Vec` and `Box` are stable. You can now give one collection a different allocator (an arena, a counting wrapper, a fixed-size pool) without nightly Rust and without rewriting the collection type. This is per-collection, unlike `#[global_allocator]`, which swaps the allocator for the whole program.

## Bad

```rust
// Hand-written collection just to track allocations
struct TrackedVec<T> {
    inner: Vec<T>,
    allocations: usize,
}

// Or a global allocator when only one collection needs special treatment
use std::alloc::System;

#[global_allocator]
static GLOBAL: System = System; // affects every allocation in the program
```

## Good

```rust
use std::alloc::{AllocError, Allocator, Global, Layout};
use std::ptr::NonNull;
use std::sync::atomic::{AtomicUsize, Ordering};

/// Counts allocations and forwards them to the global allocator.
struct Counting<'a> {
    count: &'a AtomicUsize,
}

// SAFETY: every call is forwarded unchanged to `Global`, which upholds the
// `Allocator` contract. The counter does not affect any block.
unsafe impl Allocator for Counting<'_> {
    fn allocate(&self, layout: Layout) -> Result<NonNull<[u8]>, AllocError> {
        self.count.fetch_add(1, Ordering::Relaxed);
        Global.allocate(layout)
    }

    unsafe fn deallocate(&self, ptr: NonNull<u8>, layout: Layout) {
        // SAFETY: the caller guarantees `ptr` came from `self.allocate(layout)`,
        // which forwarded to `Global`.
        unsafe { Global.deallocate(ptr, layout) }
    }
}

fn main() {
    let count = AtomicUsize::new(0);

    let mut v: Vec<u32, Counting<'_>> =
        Vec::with_capacity_in(16, Counting { count: &count });
    v.extend(0..16);
    let b = Box::new_in(7u8, Counting { count: &count });

    assert_eq!(count.load(Ordering::Relaxed), 2);
    drop((v, b));
}
```

## Notes

- `Vec<T, A>` and `Box<T, A>` carry the allocator in the type, so a function that accepts `Vec<T>` accepts only `Vec<T, Global>`. Make a function generic over `A: Allocator` only when callers need it.
- `Allocator` is an `unsafe trait`. Implementing it correctly (alignment, growth, zero-sized requests) is hard. Prefer wrapping `Global` or `System`, or use an existing crate.
- Check that an arena crate implements `std::alloc::Allocator` before relying on it. In bumpalo 3.x, the `allocator_api` feature emits `#![feature(allocator_api)]`, which stable compilers reject, and the `allocator-api2` feature implements the `allocator-api2` crate's own `Allocator` trait. Neither is a guarantee that `Vec::new_in(&bump)` works with std's `Vec`. `bumpalo::collections::Vec` is a separate type that needs none of this. See [mem-arena-allocator](mem-arena-allocator.md).
- `GlobalAlloc` and `#[global_allocator]` are unchanged. `GlobalAllocator`, `StaticAllocator`, and `AllocatorClone` are still unstable.

## See Also

- [mem-arena-allocator](mem-arena-allocator.md) - Arena allocation for batches
- [mem-with-capacity](mem-with-capacity.md) - Pre-allocate when size is known
- [unsafe-safety-comment](unsafe-safety-comment.md) - Document every unsafe impl
