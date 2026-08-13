# lint-unsafe-doc

> Require a local proof for every unsafe operation

## Why It Matters

`clippy::undocumented_unsafe_blocks` requires a `// SAFETY:` comment immediately associated with an unsafe block or implementation. The comment is not a waiver: it must connect the operation's exact preconditions to invariants established by safe construction, a preceding check, or the caller contract of an `unsafe fn`. Unsafe code can cause undefined behavior even when a comment exists, so reviews and Miri/fuzz tests remain required.

## Configuration

```toml
[lints.clippy]
undocumented_unsafe_blocks = "deny"
multiple_unsafe_ops_per_block = "warn"
missing_safety_doc = "deny"
```

Workspace lint inheritance must apply this policy to every crate containing unsafe code. Generated bindings may use a narrow, reviewed override at the generated boundary; do not weaken the workspace policy globally.

## Bad

```rust
pub fn byte_at(bytes: &[u8], index: usize) -> Option<u8> {
    if index < bytes.len() {
        // No proof is recorded next to the unchecked operation.
        Some(unsafe { *bytes.get_unchecked(index) })
    } else {
        None
    }
}
```

## Good

```rust
pub fn byte_at(bytes: &[u8], index: usize) -> Option<u8> {
    if index >= bytes.len() {
        return None;
    }

    // SAFETY: the branch above proves index < bytes.len(), and bytes is a
    // valid slice for the duration of this access.
    Some(unsafe { *bytes.get_unchecked(index) })
}
```

Prefer `bytes.get(index).copied()` unless measurement proves the checked wrapper is a real hot path and optimized output retains a redundant check.

## Unsafe Caller Contracts

```rust
/// Creates a shared slice from a raw memory region.
///
/// # Safety
///
/// For the returned lifetime `'a`, `ptr` must be non-null and properly aligned,
/// point to `len` initialized bytes in one allocation, remain valid for reads,
/// and not be mutated except through `UnsafeCell`. `len` must not exceed
/// `isize::MAX`, and `ptr.add(len)` must stay within the allocation.
pub unsafe fn bytes_from_raw<'a>(ptr: *const u8, len: usize) -> &'a [u8] {
    // SAFETY: the caller contract above is exactly the contract required by
    // from_raw_parts; this block performs no additional pointer operations.
    unsafe { std::slice::from_raw_parts(ptr, len) }
}
```

A `SAFETY` comment inside the function does not make a raw-pointer API safe. Preconditions that safe Rust cannot enforce belong in an `unsafe fn` and its `# Safety` rustdoc. Prefer accepting a slice or an owning handle whenever possible.

## Pointer Ownership

```rust
use std::ptr::NonNull;

struct Owned<T> {
    ptr: NonNull<T>,
}

impl<T> Owned<T> {
    fn new(value: T) -> Self {
        Self {
            ptr: NonNull::from(Box::leak(Box::new(value))),
        }
    }
}

impl<T> Drop for Owned<T> {
    fn drop(&mut self) {
        // SAFETY: new obtains ptr from one Box allocation; Owned keeps unique
        // ownership and reconstructs that Box exactly once during Drop.
        unsafe { drop(Box::from_raw(self.ptr.as_ptr())) };
    }
}
```

The proof covers origin, validity, uniqueness, and exactly-once reclamation. “The pointer is non-null” alone would not be sufficient.

## FFI Calls

```rust
unsafe extern "C" {
    unsafe fn consume(data: *const u8, len: usize) -> i32;
}

fn send(bytes: &[u8]) -> Result<(), i32> {
    // SAFETY: bytes.as_ptr() is valid for bytes.len() initialized bytes for the
    // duration of the call; the foreign contract promises not to retain or
    // mutate the region.
    let status = unsafe { consume(bytes.as_ptr(), bytes.len()) };
    match status {
        0 => Ok(()),
        code => Err(code),
    }
}
```

The comment must cite the reviewed foreign contract, ownership/retention policy, length units, mutability, and thread requirements that matter to the call. Validate generated declarations against the linked library version.

## Manual Send And Sync

```rust
use std::ptr::NonNull;

struct OwnedBuffer {
    ptr: NonNull<u8>,
    len: usize,
}

// SAFETY: OwnedBuffer has unique ownership of its allocation; moving the
// handle transfers that ownership, and all access requires &mut self. The
// allocator permits deallocation on a different thread.
unsafe impl Send for OwnedBuffer {}
```

Manual `Send` or `Sync` needs a concurrency proof about aliasing, mutation, ownership transfer, destruction, and the behavior of every reachable field. Bit-pattern validity or the absence of obvious pointers is not such a proof. Avoid a manual implementation when field types can encode the invariant and derive the auto traits.

## Review Checklist

1. State each unsafe operation's library or language preconditions.
2. Point to the local check, constructor invariant, or unsafe caller contract establishing each precondition.
3. Cover provenance, bounds, alignment, initialization, aliasing, lifetimes, ownership, concurrency, unwinding, and FFI retention where applicable.
4. Keep one conceptual unsafe operation per block so the proof cannot silently expand.
5. Add a regression test that exercises boundary values; use Miri for supported pure-Rust paths and sanitizers/fuzzing for compatible native boundaries.

## See Also

- [doc-safety-section](./doc-safety-section.md) - document unsafe caller and implementor obligations
- [unsafe-safety-comment](unsafe-safety-comment.md) - write precise local safety proofs
- [unsafe-minimize-scope](unsafe-minimize-scope.md) - prevent proof scope from growing
- [unsafe-miri-ci](unsafe-miri-ci.md) - run dynamic undefined-behavior checks
