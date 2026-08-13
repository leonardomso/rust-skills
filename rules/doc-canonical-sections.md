# doc-canonical-sections

> Structure public API docs as summary, details, examples, errors, panics, safety, and abort behavior where each applies

## Why It Matters

Rustdoc readers scan familiar headings to find the contract. A consistent order keeps failure behavior from disappearing below implementation notes and gives documentation tools stable sections to index. Parameters should be explained in prose around their semantics rather than copied into a mechanical table that repeats the signature.

## Bad

```rust
/// Copies bytes.
///
/// # Parameters
/// - `src`: source bytes
/// - `dst`: destination bytes
///
/// May fail or stop the process.
pub unsafe fn copy_frame(src: *const u8, dst: *mut u8, len: usize) {
    // ...
}
```

## Good

```rust
/// Copies one initialized frame into caller-owned storage.
///
/// `src` must identify `len` readable bytes and `dst` must identify `len`
/// writable bytes. The regions must not overlap.
///
/// # Examples
///
/// ```
/// let source = [1_u8, 2, 3];
/// let mut destination = [0_u8; 3];
/// destination.copy_from_slice(&source);
/// assert_eq!(destination, source);
/// ```
///
/// # Errors
///
/// A checked wrapper returns an error when either region is too short.
///
/// # Panics
///
/// The checked wrapper does not panic.
///
/// # Safety
///
/// Both pointers must be valid for `len` bytes, correctly aligned, and
/// non-overlapping for the duration of the copy.
///
/// # Aborts
///
/// With `panic = "abort"`, a violated assertion in the surrounding FFI shim
/// terminates the process instead of unwinding to the host.
pub unsafe fn copy_frame(src: *const u8, dst: *mut u8, len: usize) {
    // SAFETY: the function's caller contract requires valid, aligned,
    // non-overlapping regions for len bytes.
    unsafe { std::ptr::copy_nonoverlapping(src, dst, len) }
}
```

## Canonical Order

1. One-sentence summary.
2. Extended semantics and parameter relationships in prose.
3. `# Examples` for supported use.
4. `# Errors` for returned failures.
5. `# Panics` for conditions that unwind.
6. `# Safety` for caller or implementor obligations on unsafe APIs.
7. `# Aborts` when process termination is possible independently of unwinding.

Include only applicable sections, but do not hide an applicable failure mode by omitting its heading.

## See Also

- [doc-first-sentence](doc-first-sentence.md) - keep the summary scannable
- [doc-examples-section](doc-examples-section.md) - runnable local and end-to-end examples
- [doc-errors-section](doc-errors-section.md) - enumerate returned failures
- [doc-panics-section](doc-panics-section.md) - document contract violations that panic
- [doc-safety-section](doc-safety-section.md) - state every unsafe obligation
- [err-catch-unwind-boundary](err-catch-unwind-boundary.md) - `panic = "abort"` bypasses unwind recovery
