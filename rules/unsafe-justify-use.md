# unsafe-justify-use

> Use `unsafe` only for a novel abstraction, a measured hot path, or FFI / platform code — never as an ad-hoc shortcut

## Why It Matters

`unsafe` moves checks from the compiler to whoever writes and reviews the block. That review misses things, and a miss is how you ship a memory-safety hole. Require a listed reason before the keyword appears, and forbid sprinkling it through otherwise safe code to "just" transmute an enum, mint `Send`, or erase a lifetime. Those shortcuts are not promoted into acceptable designs merely by moving them behind a helper; the valid categories below still need a sound invariant that cannot be expressed safely.

## Bad

```rust
#[repr(u8)]
enum Kind {
    Low = 1,
    High = 2,
}

fn kind_tag(kind: Kind) -> u8 {
    unsafe { std::mem::transmute(kind) }
}

fn linger(text: &str) -> &'static str {
    unsafe { std::mem::transmute(text) }
}

struct Mailbox<T> {
    inner: *const T,
}

unsafe impl<T> Send for Mailbox<T> {}

fn main() {
    let _ = kind_tag(Kind::Low);
    let _ = linger("tmp");
}
```

## Good

```rust
#[repr(u8)]
enum Kind {
    Low = 1,
    High = 2,
}

fn kind_tag(kind: Kind) -> u8 {
    kind as u8
}

/// # Safety
///
/// `index < bytes.len()`.
pub unsafe fn byte_unchecked(bytes: &[u8], index: usize) -> u8 {
    // SAFETY: caller proved the index is in range.
    unsafe { *bytes.as_ptr().add(index) }
}

fn byte_at(bytes: &[u8], index: usize) -> Option<u8> {
    bytes.get(index).copied()
}

fn main() {
    assert_eq!(kind_tag(Kind::High), 2);
    let buf = b"ab";
    assert_eq!(byte_at(buf, 1), Some(b'b'));
    // SAFETY: index 1 is within the two-byte `buf`.
    let b = unsafe { byte_unchecked(buf, 1) };
    assert_eq!(b, b'b');
}
```

## Valid Reasons

Only these count:

1. **Novel abstraction** — a new smart pointer, arena, or similar primitive that the standard library does not already provide.
2. **Performance** — a proven hot path, typically an `_unchecked` index or a comparable elision after a bench.
3. **FFI and platform calls** — talking to C, a kernel, or an OS API.

Anything else is an ad-hoc use. Ad-hoc means the `unsafe` sits inside unrelated code instead of behind a dedicated, documented boundary.

## Key Points

**Novel abstractions**

- Search for an established crate or std type first. If it exists, use it.
- Keep the surface minimal and unit-testable.
- Treat closures as hostile: if a callback panics, the abstraction must become invalid (poisoned, consumed, or otherwise unusable), not half-updated.
- Treat every safe trait as potentially lying, especially `Deref`, `Clone`, and `Drop`.
- Every `unsafe` use needs plain-language safety reasoning (`unsafe-safety-comment`).
- The tests, including the adversarial ones, must pass [Miri](https://github.com/rust-lang/miri).
- Apply the invariants and review model documented by the [Unsafe Code Guidelines Reference](https://rust-lang.github.io/unsafe-code-guidelines/).

**Performance**

- Benchmark first (`perf-profile-first`, `test-criterion-bench`). Intuition is not a reason.
- Document safety both when *calling* an unsafe primitive and when *publishing* an `_unchecked` API.
- The path must pass Miri and the unsafe code guidelines.

**FFI**

- Prefer a maintained interop stack (`bindgen`, `windows`, `jni`, `cxx`) over hand-rolled transmutes.
- Document generated bindings so callers know which call patterns are legal.
- Still follow the unsafe code guidelines.

**Forbidden as shortcuts**

- Transmuting to "simplify" an enum or integer cast.
- `unsafe impl Send` / `Sync` (or similar auto-trait impls) to dodge a bound.
- Transmuting lifetimes to make a borrow outlive its owner.

Do not use these patterns to evade the type system. A legitimate primitive may
contain a manual auto-trait implementation or carefully bounded lifetime
machinery only when its owned representation independently proves the required
invariant; the reason is the primitive's novel capability, not the bound it
wanted to bypass. A wrapper around unconstrained `T` or a borrow extended past
its owner is unsound regardless of documentation or tests.

## See Also

- [unsafe-sound-abstractions](unsafe-sound-abstractions.md) - a justified block still has to be sound
- [unsafe-means-ub](unsafe-means-ub.md) - the keyword is for UB, not for dangerous-but-defined work
- [unsafe-safety-comment](unsafe-safety-comment.md) - write the reasoning the checklist requires
- [unsafe-miri-ci](unsafe-miri-ci.md) - run Miri in CI on every crate that contains `unsafe`
- [unsafe-send-sync-manual](unsafe-send-sync-manual.md) - manual `Send`/`Sync` is an abstraction, not a one-liner
- [perf-profile-first](perf-profile-first.md) - measure before `_unchecked`
- [test-criterion-bench](test-criterion-bench.md) - the bench that justifies a performance `unsafe`
- [ffi-logic-in-core](ffi-logic-in-core.md) - keep raw interop in the shim, not in domain code
