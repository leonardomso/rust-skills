# unsafe-sound-abstractions

> Never expose a safe function that can cause undefined behavior, and use `unsafe` only to mark UB risk

## Why It Matters

A safe function promises that no caller can trigger undefined behavior with it. If any input, however odd, can break that promise, the function is unsound, and the bug is in the function, not in its caller. When you cannot enforce the invariant yourself, expose an `unsafe fn` and document the contract. The reverse also holds: `unsafe` means "misuse risks UB". Do not use it to flag operations that are merely destructive, or the marker loses its meaning and callers learn to ignore it.

## Bad

```rust
// Unsound: safe signature, but index is never checked
pub fn byte_at(data: &[u8], index: usize) -> u8 {
    unsafe { *data.get_unchecked(index) }
}

// Unsound: lets any T cross threads
pub struct AlwaysSend<T>(pub T);
unsafe impl<T> Send for AlwaysSend<T> {}

// Misuse of unsafe: deleting data is dangerous, but it is not UB
pub unsafe fn delete_all_rows() {}
```

## Good

```rust
/// Reads the byte at `index`.
///
/// # Safety
///
/// `index` must be less than `data.len()`.
pub unsafe fn byte_at_unchecked(data: &[u8], index: usize) -> u8 {
    // SAFETY: the caller guarantees `index < data.len()`
    unsafe { *data.get_unchecked(index) }
}

// The safe wrapper checks the invariant itself, so it is sound
pub fn byte_at(data: &[u8], index: usize) -> Option<u8> {
    if index < data.len() {
        // SAFETY: `index < data.len()` was just checked
        Some(unsafe { byte_at_unchecked(data, index) })
    } else {
        None
    }
}

// Dangerous but not UB: a normal safe function, named and documented clearly
pub fn delete_all_rows() {}
```

## Module Boundaries

Soundness is judged at the module boundary. Inside one module, a safe method may rely on an invariant that the module's constructor establishes, such as a private field that always holds a valid pointer. Keep that field private so code outside the module cannot break the invariant.

## See Also

- [unsafe-safety-comment](unsafe-safety-comment.md) - Document why each block is sound
- [unsafe-minimize-scope](unsafe-minimize-scope.md) - Keep unsafe blocks small
- [unsafe-miri-ci](unsafe-miri-ci.md) - Catch undefined behavior in tests
- [unsafe-send-sync-manual](unsafe-send-sync-manual.md) - Manual `Send`/`Sync` impls need a real argument
- [doc-safety-section](doc-safety-section.md) - Document the contract of `unsafe fn`
- Source: Microsoft Pragmatic Rust Guidelines, M-UNSOUND and M-UNSAFE-IMPLIES-UB
