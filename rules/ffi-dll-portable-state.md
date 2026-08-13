# ffi-dll-portable-state

> Share only portable, repr-stable values across Rust dynamic libraries; keep allocations, statics, TLS, and TypeId local to the DLL that created them

## Why It Matters

The compiler treats each Rust dylib as its own program. That copy has its own `static`s and thread-locals, its own `TypeId` table, and its own allocator. `#[repr(Rust)]` layout is allowed to differ between those compilations. Handing a `String`, a Tokio handle, or a default-repr struct to another DLL is not "the same type": Drop may free the wrong heap, a method body may run against the wrong statics, and a `TypeId` comparison is meaningless. Allow only portable state across that edge, both when you load plugins and when you publish one.

FFI safety alone is insufficient for cross-image ownership. A portable value
also has a defined layout (`#[repr(C)]` or equivalent) and satisfies every
constraint below:

- It has no interaction with any `static` or thread-local.
- It has no interaction with any `TypeId`.
- It contains no value, pointer, or reference to non-portable data.

A pointer *into* portable bytes that still live in a non-portable owner is allowed: a `*const u8` / length pair into a `Vec<u8>` that the allocating DLL keeps is portable; the `Vec` itself is not. *Interaction* is any computational relationship, including how the bits are interpreted. Passing a `u128` is fine; transmuting a `TypeId` into that `u128` is not.

## Bad

```rust
pub struct Meter {
    label: String,
}

impl Meter {
    pub fn reading(&self) -> u64 {
        // Resolved in *this* crate. Across a DLL boundary the bytes
        // behind `self` were laid out by the other image, but this
        // method still uses this image's statics and TypeId table.
        self.label.len() as u64
    }
}

pub unsafe fn drive(meter: *const Meter) -> u64 {
    // SAFETY: demonstration only — the type is not portable.
    unsafe { (*meter).reading() }
}

fn main() {
    let meter = Meter {
        label: String::from("pump"),
    };
    let n = unsafe { drive(&meter) };
    assert_eq!(n, 4);
}
```

## Good

```rust
#[repr(C)]
pub struct Sample {
    pub millis: u32,
    pub value: i32,
}

#[repr(C)]
pub struct ByteView {
    pub ptr: *const u8,
    pub len: usize,
}

/// # Safety
///
/// `view.ptr` must be valid for `view.len` bytes until this function
/// returns. The caller keeps the allocation and the matching allocator;
/// this side must copy if it needs the bytes later.
pub unsafe fn checksum(view: ByteView) -> u32 {
    if view.ptr.is_null() {
        return 0;
    }
    // SAFETY: caller owns the buffer for the duration of the call.
    let bytes = unsafe { std::slice::from_raw_parts(view.ptr, view.len) };
    bytes.iter().fold(0u32, |acc, b| acc.wrapping_add(u32::from(*b)))
}

pub type FillSample = unsafe extern "C" fn(*mut Sample) -> i32;

unsafe extern "C" fn fill_zero(out: *mut Sample) -> i32 {
    if out.is_null() {
        return 1;
    }
    // SAFETY: non-null `out` is a live `Sample` the caller owns.
    unsafe {
        *out = Sample {
            millis: 0,
            value: 0,
        };
    }
    0
}

fn main() {
    let owned = b"ok";
    let view = ByteView {
        ptr: owned.as_ptr(),
        len: owned.len(),
    };
    // SAFETY: `view` points to `owned`, which remains live for this call.
    let sum = unsafe { checksum(view) };
    assert_eq!(sum, u32::from(b'o') + u32::from(b'k'));

    let fill: FillSample = fill_zero;
    let mut sample = Sample {
        millis: 9,
        value: 4,
    };
    // SAFETY: `sample` is live and uniquely borrowed for this call.
    let rc = unsafe { fill(&mut sample) };
    assert_eq!(rc, 0);
    assert_eq!(sample.millis, 0);
}
```

## Key Points

- **Allocator ownership.** `String`, `Vec<T>`, `Box<T>`, and anything else that frees on drop must be dropped by the DLL that allocated them. Crossing the boundary is a cross-heap free.
- **Transitive portability.** Every nested field must be portable. Wrapping a `String` in `#[repr(C)]` does not make the heap value portable.
- **Nested pointers.** A pointer or reference is portable only when it addresses portable data. Pointing at a Rust-layout node inside a C envelope is still UB.
- **Byte views need a protocol.** A slice or `ptr`+`len` view is portable for primitive bytes; document who allocated, who copies, who frees, and that the owner outlives the call.
- **Hidden method hazard.** A method call on a foreign object is compiled in *your* image. The code that runs is yours; the bytes are theirs. Prefer an `extern "C"` function pointer the originating DLL provides.
- **Libraries with process state.** Runtimes and loggers that keep static registries (`tokio`, `log`, similar) are not portable handles. Give each DLL its own instance, or talk through a C ABI you control.
- Passing any of the above across libraries is how you get silent data loss, corrupted state, and usually undefined behavior.

## See Also

- [ffi-logic-in-core](ffi-logic-in-core.md) - translate at the boundary; do not ship domain types as C layouts
- [ffi-native-escape-hatch](ffi-native-escape-hatch.md) - documented raw conversions stay on the wrapper
- [type-repr-transparent](type-repr-transparent.md) - a one-field ABI wrapper is layout-stable; a Rust struct is not
- [proj-avoid-statics](proj-avoid-statics.md) - process-identity state is already unsound inside one binary
- [conc-thread-local](conc-thread-local.md) - TLS is per image, not per process
- [unsafe-minimize-scope](unsafe-minimize-scope.md) - the only `unsafe` at the edge should be the pointer copies
