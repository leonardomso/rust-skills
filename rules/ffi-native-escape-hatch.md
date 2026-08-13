# ffi-native-escape-hatch

> Give native-handle wrappers `from_native` / `into_native` / `as_native` so FFI code can cross the boundary without leaking the raw type everywhere

## Why It Matters

A safe `WindowId` that hides the OS value is useless the moment a caller already has a HWND from C, or must pass yours into another library. Provide a documented conversion pair: `from_native` states the ownership and validity rules, while `into_native` or `as_native` gives the integer or pointer back. Keep those methods on the wrapper; do not publish the raw type as the crate's currency (`ffi-logic-in-core`).

## Bad

```rust
// Public field plus an ad-hoc getter: callers poke the raw HWND and
// skip any ownership contract.
pub struct WindowId {
    pub raw: usize,
}

impl WindowId {
    pub fn new(raw: usize) -> Self {
        Self { raw }
    }

    pub fn hwnd(&self) -> usize {
        self.raw
    }
}
```

## Good

```rust
pub struct WindowId(usize);

impl WindowId {
    pub fn new(raw: usize) -> Self {
        Self(raw)
    }

    /// # Safety
    ///
    /// `raw` must be a live window handle this process owns, and no
    /// other `WindowId` may wrap the same value.
    pub unsafe fn from_native(raw: usize) -> Self {
        Self(raw)
    }

    pub fn into_native(self) -> usize {
        self.0
    }

    pub fn as_native(&self) -> usize {
        self.0
    }
}

fn main() {
    let window = WindowId::new(0x100);
    assert_eq!(window.as_native(), 0x100);
    let raw = window.into_native();
    // SAFETY: `raw` came from the sole owning wrapper and has not been reused.
    let _ = unsafe { WindowId::from_native(raw) };
}
```

## See Also

- [ffi-logic-in-core](ffi-logic-in-core.md) - the escape hatch lives on the wrapper, not on the domain type
- [type-repr-transparent](type-repr-transparent.md) - a newtype around the native integer stays ABI-compatible
- [unsafe-safety-comment](unsafe-safety-comment.md) - `from_native` is `unsafe`; write the `# Safety` contract
