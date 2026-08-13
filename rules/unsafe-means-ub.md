# unsafe-means-ub

> Mark a function or trait `unsafe` only when misuse can cause undefined behavior, not because it is merely dangerous

## Why It Matters

`unsafe` is a contract about the abstract machine: use this wrong and you may get a data race, a wild pointer, or a broken validity invariant. Using it as a "this is scary" sticker trains callers to sprinkle `unsafe {}` around destructive operations. `unsafe` is for UB risk only. A function that reboots a host, spends money, or pages on-call stays safe, gets a loud name, and documents the blast radius. The same test applies to traits: an `unsafe trait` means an incorrect implementation can let safe code cause UB.

## Bad

```rust
pub unsafe fn reboot_host(host: &str) {
    let _ = host;
}

pub fn restart(host: &str) {
    // Callers now need an unsafe block for a defined, if catastrophic, action.
    unsafe { reboot_host(host) }
}
```

## Good

```rust
/// Immediately restarts `host`.
///
/// This cannot cause undefined behavior. It *can* destroy production data.
/// Callers must pass a host they have already authorized to restart.
pub fn reboot_host(host: &str) {
    let _ = host;
}

/// # Safety
///
/// `ptr` must be valid for a `u32` read.
pub unsafe fn read_u32(ptr: *const u32) -> u32 {
    // SAFETY: caller promised `ptr` is aligned and dereferenceable.
    unsafe { ptr.read() }
}

fn main() {
    reboot_host("worker-7");
    let value = 7u32;
    // SAFETY: `value` is a live, aligned `u32` for this call.
    let n = unsafe { read_u32(&value) };
    assert_eq!(n, 7);
}
```

## Key Points

- The test is undefined behavior, not consequences: data races, invalid derefs, and aliasing violations are `unsafe`; deleting data or spending money is not.
- Dangerous-but-defined operations stay safe, use a loud name, and document the blast radius.
- Mark a trait `unsafe` only when safe code relies on every implementation upholding invariants that prevent UB; document those implementation obligations.

## See Also

- [unsafe-safety-comment](unsafe-safety-comment.md) - document the UB preconditions, not the business risk
- [doc-safety-section](doc-safety-section.md) - `# Safety` belongs on `unsafe fn`, not on a safe foot-gun
- [err-result-over-panic](err-result-over-panic.md) - defined failures still return `Result`
