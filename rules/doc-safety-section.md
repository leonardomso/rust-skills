# doc-safety-section

> Document every caller or implementor obligation of unsafe APIs

## Why It Matters

An `unsafe fn` or `unsafe trait` shifts proof obligations to its caller or implementor. A `# Safety` section must state every condition required to avoid undefined behavior, using the vocabulary of the operation: provenance, allocation, bounds, alignment, initialization, aliasing, lifetime, ownership, thread behavior, unwinding, and foreign retention. The section is part of the public contract; an incomplete contract cannot be repaired by a comment inside the implementation.

## Bad

```rust
/// Reads a value from a raw pointer.
pub unsafe fn take_ptr<T>(ptr: *const T) -> T {
    // Missing caller contract and missing local unsafe block in Rust 2024.
    ptr.read()
}
```

## Good

```rust
/// Moves one initialized `T` out of `ptr` without dropping the source slot.
///
/// # Safety
///
/// `ptr` must be non-null, properly aligned, and valid for reading one
/// initialized `T`. The caller must own that value and must treat the source
/// slot as uninitialized after this call: it must not read or drop the old
/// value again. No access that conflicts with this read may occur during the
/// call. The allocation itself remains the caller's responsibility.
pub unsafe fn take_ptr<T>(ptr: *const T) -> T {
    // SAFETY: the caller contract establishes ptr::read's validity, alignment,
    // initialization, aliasing, and ownership requirements.
    unsafe { ptr.read() }
}
```

If the API only needs a copy, accept `&T` and require `T: Copy`. If it only needs to inspect a value, return a borrow tied to an input reference/owner instead of inventing a lifetime from a raw pointer.

## Raw Ownership Reconstruction

```rust
/// Reclaims a value previously returned by `Box::into_raw`.
///
/// # Safety
///
/// `ptr` must be the exact non-null pointer returned by `Box::into_raw` for a
/// `Box<T>` allocated by the allocator used by this program. Ownership must
/// not already have been reclaimed or transferred. After this call the caller
/// must not dereference, free, or otherwise use `ptr`.
pub unsafe fn reclaim_box<T>(ptr: *mut T) {
    // SAFETY: the caller contract is exactly Box::from_raw's ownership and
    // allocation-origin contract; the reconstructed Box is dropped once.
    unsafe { drop(Box::from_raw(ptr)) };
}
```

Reconstructing `Vec` or `String` from `(ptr, len, cap)` has additional exact layout/capacity and UTF-8 requirements that are easy to under-document. Prefer transferring an owning handle. When raw parts are unavoidable, mirror the current standard-library contract completely and test the exact producer/consumer pair.

## Unsafe Traits

```rust
/// Marker for types for which an all-zero byte pattern is a valid value.
///
/// # Safety
///
/// Implementors must guarantee that a value whose entire object representation
/// is zero satisfies every validity invariant of `Self`.
pub unsafe trait ZeroValid {}

// SAFETY: every bit pattern is valid for u32, including all-zero (0).
unsafe impl ZeroValid for u32 {}

pub fn zeroed<T: ZeroValid>() -> T {
    // SAFETY: the unsafe trait contract guarantees the all-zero representation
    // produced here is a valid T.
    unsafe { std::mem::MaybeUninit::<T>::zeroed().assume_init() }
}
```

This contract says nothing about safely serializing padding, transmuting between types, plain-old-data layout, or FFI ABI. Add separate traits/contracts only when those properties are needed. Prefer established audited crates for byte-casting abstractions.

## Unsafe Blocks In Safe Functions

```rust
pub fn get<T>(data: &[T], index: usize) -> Option<&T> {
    if index >= data.len() {
        return None;
    }

    // SAFETY: the branch proves index < data.len(); data is a valid shared
    // slice for the returned borrow's lifetime.
    Some(unsafe { data.get_unchecked(index) })
}
```

Use `data.get(index)` unless optimized-code inspection and measurement show a retained redundant check. A safe wrapper must establish every precondition itself; it cannot put “the caller must ensure” in a normal comment.

## FFI Additions

For foreign calls, document:

- exact ABI, header/library version, calling convention, and target assumptions;
- pointer/length units, nullability, mutability, alignment, and initialization;
- whether the callee retains pointers or calls back, and for how long;
- ownership and allocator for returned/transferred memory;
- thread affinity, synchronization, errno/last-error capture, and error codes;
- unwind/exception policy in both directions;
- shutdown and library-unload behavior.

Keep the foreign declaration and unsafe call behind a safe adapter that validates what Rust can enforce.

## Review Checklist

1. Copy each operation's normative safety requirements, then specialize them to the API.
2. Explain how the implementation establishes its own local unsafe preconditions.
3. State what becomes invalid or changes ownership after success and failure.
4. Cover zero-length/dangling-pointer rules and integer overflow in pointer ranges.
5. Add Miri tests for supported Rust-only paths plus sanitizer/fuzz/cross-language tests for native boundaries.
6. Treat a changed `# Safety` section as a compatibility and security review.

## See Also

- [lint-unsafe-doc](./lint-unsafe-doc.md) - enforce and review local unsafe proofs
- [unsafe-safety-comment](unsafe-safety-comment.md) - connect contract to operation
- [unsafe-minimize-scope](unsafe-minimize-scope.md) - keep proof boundaries narrow
- [ffi-logic-in-core](ffi-logic-in-core.md) - isolate unsafe foreign adapters
