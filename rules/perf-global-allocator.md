# perf-global-allocator

> Pick the process global allocator on purpose in application crates; leave libraries on the system default

## Why It Matters

Library crates must not install a `#[global_allocator]`: the application owns the process heap, and two crates fighting over it is a link error. The system allocator is a fine default; replacing it is a measured application decision for allocation-heavy workloads. `mimalloc`, `jemalloc`, `snmalloc`, and the system heap are all candidates once representative benchmarks justify one. Put the `static` in `main.rs`, never in a published `lib.rs`.

## Bad

```rust
// inside a library crate
use std::alloc::{GlobalAlloc, Layout, System};

struct LibHeap;

unsafe impl GlobalAlloc for LibHeap {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        // SAFETY: this implementation forwards the allocator contract unchanged.
        unsafe { System.alloc(layout) }
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        // SAFETY: callers must pass the pointer and layout returned by this allocator.
        unsafe { System.dealloc(ptr, layout) }
    }
}

#[global_allocator]
static LIB_HEAP: LibHeap = LibHeap;
```

## Good

```rust
// src/main.rs of an application
use std::alloc::{GlobalAlloc, Layout, System};

struct AppHeap;

unsafe impl GlobalAlloc for AppHeap {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        // Production apps often swap `System` for `mimalloc::MiMalloc` here
        // after a benchmark; the choice stays in the binary, not a library.
        // SAFETY: this implementation forwards the allocator contract unchanged.
        unsafe { System.alloc(layout) }
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        // SAFETY: callers must pass the pointer and layout returned by this allocator.
        unsafe { System.dealloc(ptr, layout) }
    }
}

#[global_allocator]
static HEAP: AppHeap = AppHeap;

fn main() {
    let _v = vec![1, 2, 3];
}
```

## See Also

- [proj-lib-main-split](proj-lib-main-split.md) - the allocator static lives next to `main`, not in `lib.rs`
- [perf-profile-first](perf-profile-first.md) - change the heap only after a profile says allocation is the cost
- [mem-arena-allocator](mem-arena-allocator.md) - scoped arenas are a library-safe alternative to a process-global swap
