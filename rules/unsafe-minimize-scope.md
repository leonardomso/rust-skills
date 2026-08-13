# unsafe-minimize-scope

> Keep each unsafe block limited to operations covered by one local proof

## Why It Matters

`unsafe fn` marks a caller contract; it does not make every operation in the body implicitly reviewed. The `unsafe_op_in_unsafe_fn` lint requires explicit unsafe blocks for unsafe operations when enabled and is warn-by-default in the Rust 2024 edition, not a language hard error. Deny it in workspace policy. Small blocks keep the proof next to the exact operation and prevent later safe logic from silently entering the trusted surface.

## Configuration

```toml
[workspace.lints.rust]
unsafe_op_in_unsafe_fn = "deny"

[workspace.lints.clippy]
undocumented_unsafe_blocks = "deny"
multiple_unsafe_ops_per_block = "warn"
```

## Bad

```rust
/// # Safety
///
/// `ptr` must identify `len` initialized bytes in one allocation.
pub unsafe fn copy_bytes(ptr: *const u8, len: usize) -> Vec<u8> {
    unsafe {
        let mut output = Vec::with_capacity(len); // Safe policy hidden inside.
        for index in 0..len {
            output.push(*ptr.add(index)); // Repeats pointer proof per element.
        }
        output
    }
}
```

The block includes allocation, loop control, and mutation even though only pointer-to-slice construction requires a caller proof. The contract is also incomplete.

## Good

```rust
/// Copies a raw byte region into an owned vector.
///
/// # Safety
///
/// `ptr` must be non-null and valid for reads of `len` initialized bytes in a
/// single allocation for the duration of this call. `len` must not exceed
/// `isize::MAX`, and `ptr.add(len)` must remain within that allocation. No
/// mutation that conflicts with these reads may occur during the call.
pub unsafe fn copy_bytes(
    ptr: *const u8,
    len: usize,
) -> Result<Vec<u8>, std::collections::TryReserveError> {
    // SAFETY: the caller contract is exactly from_raw_parts' pointer, range,
    // initialization, and aliasing contract for this temporary shared slice.
    let bytes = unsafe { std::slice::from_raw_parts(ptr, len) };

    let mut output = Vec::new();
    output.try_reserve_exact(bytes.len())?;
    output.extend_from_slice(bytes);
    Ok(output)
}
```

The safe allocation/copy policy remains outside the unsafe block and reports reservation failure. Prefer accepting `&[u8]` directly; expose the raw entry only at an FFI/platform boundary that cannot supply a Rust slice.

## Safe Wrappers Establish Preconditions

```rust
pub fn checked_value(values: &[i32], index: usize) -> Option<i32> {
    values.get(index)?.checked_add(1)
}
```

A safe function taking `(ptr, len)` cannot prove that caller-supplied raw memory is valid merely by checking `index < len`. If pointer validity remains a caller obligation, the function is unsafe. Do not use an unsafe block to hide that obligation inside a nominally safe wrapper.

## One Proof Per Block

```rust
// SAFETY: src and dst are valid for len bytes, do not overlap, and dst is
// writable and unaliased for the call.
unsafe { std::ptr::copy_nonoverlapping(src, dst, len) };

// SAFETY: out was allocated for len bytes by this allocator and the foreign
// operation initialized exactly len bytes before returning success.
let initialized = unsafe { std::slice::from_raw_parts(out, len) };
```

Separate blocks when operations rely on different facts, especially across a foreign call or state transition. A single block can contain tightly coupled operations only when one comment proves all of them and intervening safe code cannot invalidate the proof.

## Review Rules

- Keep arithmetic, bounds checks, allocation, logging, error mapping, and callbacks outside unsafe blocks.
- Use checked arithmetic before pointer offsets and cover zero-length pointer rules explicitly.
- Prefer safe standard operations (`get`, slice copy, `MaybeUninit`, `NonNull`) before unchecked primitives.
- Every `unsafe fn` needs a complete `# Safety` section even when its body delegates to another unsafe API.
- Every unsafe block needs a local `SAFETY` proof; referring only to “validated above” is insufficient when later code can change the fact.
- Run Miri on supported Rust-only paths and use sanitizer/fuzz/cross-language tests for native boundaries.

## See Also

- [unsafe-safety-comment](unsafe-safety-comment.md) - state exact local proofs
- [doc-safety-section](doc-safety-section.md) - document caller and implementor contracts
- [lint-unsafe-doc](lint-unsafe-doc.md) - enforce unsafe documentation
- [unsafe-sound-abstractions](unsafe-sound-abstractions.md) - never hide a UB precondition in safe APIs
