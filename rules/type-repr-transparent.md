# type-repr-transparent

> Use `#[repr(transparent)]` for newtypes in FFI contexts

## Why It Matters

`#[repr(transparent)]` guarantees a newtype has the same memory layout as its inner type. This is essential for FFI where you need type safety in Rust but must match C ABI layouts. Without it, the compiler may add padding or change layout.

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
use std::ffi::c_void;

// Guaranteed same layout as inner type
#[repr(transparent)]
struct Handle(u64);

// Safe for FFI
unsafe extern "C" {
    fn process_handle(h: Handle);  // Works - same layout as u64
}

// FFI pointer wrapper
#[repr(transparent)]
struct SafePointer(*mut c_void);

impl SafePointer {
    // Safe Rust API around raw pointer
    pub fn new(ptr: *mut c_void) -> Option<Self> {
        if ptr.is_null() {
            None
        } else {
            Some(SafePointer(ptr))
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

// Same ABI - can pass where f64 expected
extern "C" fn measure(distance: Meters) {}
```

## With PhantomData

```rust
use std::marker::PhantomData;

// PhantomData is zero-sized, doesn't affect layout
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
    use std::os::raw::c_int;
    
    #[repr(transparent)]
    pub struct FileDescriptor(c_int);
    
    // Hypothetical C library. Avoid libc's own names (`open`, `read`): declaring them
    // with a different signature trips the deny-by-default
    // `invalid_runtime_symbol_definitions` lint (Rust 1.98+).
    unsafe extern "C" {
        pub fn device_open(path: *const std::os::raw::c_char, flags: c_int) -> FileDescriptor;
        pub fn device_close(fd: FileDescriptor) -> c_int;
        pub fn device_read(fd: FileDescriptor, buf: *mut u8, len: usize) -> isize;
    }
}

// Safe wrapper
pub struct File {
    fd: ffi::FileDescriptor,
}

impl File {
    pub fn open(path: &str) -> std::io::Result<Self> {
        let c_path = std::ffi::CString::new(path)?;
        let fd = unsafe { ffi::device_open(c_path.as_ptr(), 0) };
        // ... error handling
        Ok(File { fd })
    }
}
```

## Version Notes

- Rust 1.98 is stricter about which fields a `repr(transparent)` type may ignore as "trivial" (zero-sized, alignment 1). `repr(C)` types, types with private fields, and `#[non_exhaustive]` types no longer count, so a wrapper whose extra field is one of those stops compiling. `PhantomData<T>` and plain `()` fields are still fine.
- Rust 1.100 warns when the same representation is specified more than once, as in `#[repr(C)] #[repr(C)]` or `#[repr(C, C)]`. Specify each one once; combine different hints in one attribute, such as `#[repr(C, align(8))]`.

## When to Use

| Scenario | Use `#[repr(transparent)]`? |
|----------|----------------------------|
| FFI newtype wrappers | Yes |
| Type-safe handles | Yes |
| NonZero optimization | Yes |
| Pure Rust newtypes | Optional (doesn't hurt) |
| Multi-field structs | N/A (only for single-field) |

## See Also

- [type-newtype-ids](./type-newtype-ids.md) - Newtype pattern
- [type-phantom-marker](./type-phantom-marker.md) - PhantomData usage
- [api-newtype-safety](./api-newtype-safety.md) - Type-safe newtypes
