# unsafe-send-sync-manual

> Manually implement `Send` or `Sync` only with a complete ownership and concurrency proof

## Why It Matters

`Send` and `Sync` are unsafe auto traits used by other unsafe code. `Send` means ownership of a value may move to another thread. `Sync` means shared references `&T` may be used from multiple threads (`T: Sync` implies `&T: Send`). A wrong implementation lets entirely safe callers create data races or violate foreign thread-affinity rules. Field changes can invalidate the proof without touching the impl, so manual implementations are a load-bearing review boundary.

## Bad

```rust
use std::cell::Cell;

struct SharedCounter {
    value: Cell<u32>,
}

unsafe impl Sync for SharedCounter {}
```

`Cell` permits non-atomic mutation through `&self`; declaring `Sync` allows concurrent shared references to race.

```rust
struct BorrowedHandle {
    ptr: *mut ForeignObject,
}

// No ownership, lifetime, aliasing, callback, destruction, or foreign
// thread-affinity proof.
unsafe impl Send for BorrowedHandle {}
unsafe impl Sync for BorrowedHandle {}
```

## Prefer Auto Traits

```rust
use std::sync::{Arc, Mutex};

struct SafeCounter {
    value: Mutex<u64>,
}

fn shared_counter() -> Arc<SafeCounter> {
    Arc::new(SafeCounter {
        value: Mutex::new(0),
    })
}
```

The field types encode synchronization, so the compiler derives the appropriate traits. Still define poison/error and overflow policy in methods; auto traits prove thread transfer, not business correctness.

## Deliberate Opt-Out Marker

```rust
use std::marker::PhantomData;
use std::ptr::NonNull;

struct ThreadAffineHandle {
    ptr: NonNull<ForeignObject>,
    // Raw pointers are !Send and !Sync; the marker prevents auto traits even if
    // the stored representation later changes to a Send integer handle.
    _thread_affine: PhantomData<*mut ()>,
}
```

Stable Rust has no general stable negative impl syntax for application types. A private raw-pointer marker is a common opt-out, but document its purpose and assert the intended auto-trait contract in compile tests.

## Documented `Send` Implementation

```rust
use std::ptr::NonNull;

struct OwnedBuffer {
    ptr: NonNull<u8>,
    len: usize,
}

impl OwnedBuffer {
    fn from_boxed(bytes: Box<[u8]>) -> Self {
        let len = bytes.len();
        let ptr = NonNull::new(Box::into_raw(bytes) as *mut u8)
            .expect("Box<[u8]> yields a non-null pointer");
        Self { ptr, len }
    }

    fn as_mut_slice(&mut self) -> &mut [u8] {
        // SAFETY: the constructor transfers unique ownership; &mut self
        // prevents another safe access for the returned lifetime.
        unsafe { std::slice::from_raw_parts_mut(self.ptr.as_ptr(), self.len) }
    }
}

impl Drop for OwnedBuffer {
    fn drop(&mut self) {
        let slice = std::ptr::slice_from_raw_parts_mut(self.ptr.as_ptr(), self.len);
        // SAFETY: slice is the exact allocation returned by Box::into_raw and
        // OwnedBuffer reconstructs it exactly once during Drop.
        unsafe { drop(Box::from_raw(slice)) };
    }
}

// SAFETY: OwnedBuffer uniquely owns the boxed allocation; moving the struct
// transfers that ownership, no safe alias escapes, u8 is Send, and the global
// allocator permits deallocation on a different thread.
unsafe impl Send for OwnedBuffer {}
```

This example intentionally does not implement `Sync`. If shared access is needed, redesign around safe synchronization or prove every shared method, callback, foreign API, and destructor is thread-safe. “All methods currently take `&mut self`” is fragile evidence by itself because future methods and public raw handles can expand the surface.

## Proof Checklist

For `Send`, establish:

- ownership and all reachable data move together;
- no borrowed pointer outlives its source and no alias retains thread-affine access;
- destruction and allocator/foreign release are allowed on the destination thread;
- callbacks, TLS, event loops, and OS handles have no origin-thread requirement.

For `Sync`, additionally establish:

- every operation reachable through `&T` is data-race-free;
- interior mutation uses correct atomics/locks and memory ordering;
- returned references/guards preserve aliasing and lifetime rules;
- foreign libraries permit concurrent calls and define shutdown/unload ordering.

For both:

- include generic bounds (`T: Send`/`Sync`) that the proof requires;
- keep fields private and constructors invariant-preserving;
- add compile-time assertions for intended positive/negative auto traits;
- run Loom for small instrumented synchronization models, Miri where supported, and stress/sanitizer tests as supplementary evidence;
- re-review the unsafe impl whenever fields, methods, allocator, target, or foreign version changes.

## See Also

- [unsafe-safety-comment](unsafe-safety-comment.md) - connect the proof to the impl
- [lint-unsafe-doc](lint-unsafe-doc.md) - enforce local unsafe documentation
- [type-phantom-marker](type-phantom-marker.md) - model ownership and variance deliberately
- [own-arc-shared](own-arc-shared.md) - shared ownership does not create thread safety
