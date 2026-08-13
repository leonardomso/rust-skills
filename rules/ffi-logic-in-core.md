# ffi-logic-in-core

> Keep business logic in a safe core crate; limit the `*-ffi` crate to translating pointers and status codes

## Why It Matters

C ABI types (`*mut u8`, lengths, integer status codes) do not compose with idiomatic Rust ownership. Once `Receipt` itself stores a raw pointer, every Rust caller inherits FFI unsafety. Split the work: a safe crate owns the data model and fallible operations; the FFI crate copies bytes across the boundary and returns a status code. The extra types are cheaper than infecting the core crate with `#[repr(C)]` layouts.

## Bad

```rust
#[repr(C)]
pub struct Receipt {
    pub merchant: [u8; 8],
    pub body_ptr: *mut u8,
    pub body_len: usize,
    pub body_cap: usize,
}

impl Receipt {
    pub fn post(&self) -> Result<(), &'static str> {
        if self.body_ptr.is_null() && self.body_len != 0 {
            return Err("null payload");
        }
        Ok(())
    }
}
```

## Good

```rust
pub struct Receipt {
    merchant: [u8; 8],
    body: Vec<u8>,
}

impl Receipt {
    pub fn new(merchant: [u8; 8], body: Vec<u8>) -> Self {
        Self { merchant, body }
    }

    pub fn post(&self) -> Result<(), &'static str> {
        let _ = self.merchant;
        if self.body.is_empty() {
            return Err("empty payload");
        }
        Ok(())
    }
}

/// FFI shim: copy the C buffers, then call the safe API.
///
/// # Safety
///
/// `merchant` must point to a live identifier. `body` must be null when
/// `body_len` is zero or valid for `body_len` readable bytes.
pub unsafe fn post_receipt(
    merchant: *const [u8; 8],
    body: *const u8,
    body_len: usize,
) -> u8 {
    if merchant.is_null() || (body.is_null() && body_len != 0) {
        return 1;
    }
    // SAFETY: caller promised `merchant` points to a live identifier.
    let dest = unsafe { *merchant };
    // SAFETY: caller promised `body` is valid for `body_len` bytes.
    let bytes = unsafe { std::slice::from_raw_parts(body, body_len) }.to_vec();
    match Receipt::new(dest, bytes).post() {
        Ok(()) => 0,
        Err(_) => 1,
    }
}

fn main() {
    let dest = [0u8; 8];
    let payload = b"ok";
    // SAFETY: both pointers refer to live local values for the duration of the call.
    let rc = unsafe { post_receipt(&dest, payload.as_ptr(), payload.len()) };
    assert_eq!(rc, 0);
}
```

## See Also

- [ffi-sys-vs-ffi-name](ffi-sys-vs-ffi-name.md) - name the translation crate `*-ffi`, not the core crate
- [type-repr-transparent](type-repr-transparent.md) - wrap a single FFI integer in the shim, not in the domain type
- [unsafe-minimize-scope](unsafe-minimize-scope.md) - the only `unsafe` should be the pointer copies at the edge
- [unsafe-safety-comment](unsafe-safety-comment.md) - document the C-side contract next to the shim
- [ffi-native-escape-hatch](ffi-native-escape-hatch.md) - from_native/into_native stay on the wrapper
- [ffi-sys-crate-builds](ffi-sys-crate-builds.md) - hermetic -sys builds, no host-tool surprise
