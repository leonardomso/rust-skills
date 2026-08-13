# type-repr-transparent

> Use `#[repr(transparent)]` for newtypes in FFI contexts

## Why It Matters

For a valid transparent struct, `#[repr(transparent)]` gives the wrapper the
layout and ABI of its one non-zero-sized field. Every other field must be
zero-sized with alignment 1. This is
useful when an FFI contract names that underlying C representation. It does not
validate values, ownership, provenance, or calling preconditions, and it does
not make the wrapper interchangeable with the field in Rust's type system.

## Bad

```rust
// No layout guarantee - might not match inner type in FFI
struct Handle(u64);

// Passing to C code might fail
unsafe extern "C" {
    fn process_handle(h: Handle);  // May not work correctly
}

// Wrapping C type without layout guarantee
struct SafePointer(*mut c_void);
```

## Good

```rust
// Guaranteed same layout as inner type
#[repr(transparent)]
struct Handle(u64);

// ABI-compatible with a C uint64_t parameter. The call remains unsafe unless
// every value and effect is safe for arbitrary Rust callers.
unsafe extern "C" {
    fn process_handle(h: Handle);
}

// Non-null is only one invariant; do not call this pointer safe.
#[repr(transparent)]
struct NonNullForeign(*mut std::ffi::c_void);

impl NonNullForeign {
    pub fn new(ptr: *mut std::ffi::c_void) -> Option<Self> {
        if ptr.is_null() {
            None
        } else {
            Some(Self(ptr))
        }
    }
}
```

## What repr(transparent) Guarantees

```rust
use std::mem::{size_of, align_of};

#[repr(transparent)]
struct Meters(f64);

// Same size
assert_eq!(size_of::<Meters>(), size_of::<f64>());

// Same alignment
assert_eq!(align_of::<Meters>(), align_of::<f64>());

// A C declaration for this parameter uses the field's compatible C type.
extern "C" fn measure(distance: Meters) { ... }
```

## With PhantomData

```rust
use std::marker::PhantomData;

// PhantomData is zero-sized and alignment 1.
#[repr(transparent)]
struct TypedHandle<T> {
    raw: u64,
    _marker: PhantomData<T>,  // Zero-sized, ignored for layout
}

// Still same layout as u64
assert_eq!(size_of::<TypedHandle<String>>(), size_of::<u64>());
```

## NonZero Wrappers

```rust
use std::num::NonZeroU64;

#[repr(transparent)]
struct NonZeroHandle(NonZeroU64);

// Inherits null-pointer optimization
assert_eq!(size_of::<Option<NonZeroHandle>>(), size_of::<u64>());
```

## FFI Pattern

```rust
mod ffi {
    use std::ffi::c_int;

    #[repr(transparent)]
    #[derive(Clone, Copy)]
    pub struct WidgetId(pub(super) u64);

    unsafe extern "C" {
        pub fn widget_enable(id: WidgetId) -> c_int;
    }
}

pub fn enable(id: ffi::WidgetId) -> Result<(), EnableError> {
    // SAFETY: the pinned C contract accepts every u64 ID by value, retains no
    // Rust memory, does not call back, and reports failure through the status.
    match unsafe { ffi::widget_enable(id) } {
        0 => Ok(()),
        status => Err(EnableError::Status(status)),
    }
}
```

## When to Use

| Scenario | Use `#[repr(transparent)]`? |
|----------|----------------------------|
| FFI newtype that must use its field's ABI | Yes, after cross-language validation |
| Pure-Rust type-safe handle | No unless representation is a separate contract |
| Stable niche/layout contract around `NonZero*` | Yes when the layout guarantee is required |
| Pure Rust newtypes | Only when layout is intentionally part of the contract |
| Multi-field structs | N/A (only for single-field) |

## See Also

- [type-newtype-ids](./type-newtype-ids.md) - Newtype pattern
- [type-phantom-marker](./type-phantom-marker.md) - PhantomData usage
- [api-newtype-safety](./api-newtype-safety.md) - Type-safe newtypes
- [ffi-logic-in-core](./ffi-logic-in-core.md) - Keep FFI layouts in the shim crate
