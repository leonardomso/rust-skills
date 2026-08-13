# unsafe-sound-abstractions

> Never expose a safe API that can hit undefined behavior; if the caller must uphold a UB precondition, the function is `unsafe`

## Why It Matters

*Safe* and `unsafe` are technical terms. A function is safe when its signature is not marked `unsafe`. That function can still be disastrous (`trigger_cluster_failover`) and an `unsafe` one can be routine (`slice.get_unchecked`) when the caller keeps the contract. A function is *unsound* when it looks safe — it is not marked `unsafe` — but *any* way of calling it from safe code, including a remote, theoretical path that needs unusual inputs, can produce undefined behavior. Give that test no slack: unsound abstractions are never allowed.

If the invariant cannot be established inside your API, do not hide it. Mark the entry `unsafe`, write the `# Safety` contract, and let the caller take the obligation.

## Bad

```rust
pub fn word_bits<T>(value: &T) -> &u64 {
    unsafe { &*(value as *const T as *const u64) }
}

pub struct Carry<T>(T);

unsafe impl<T> Send for Carry<T> {}
unsafe impl<T> Sync for Carry<T> {}

fn main() {
    let n = 1u8;
    let _ = word_bits(&n);
}
```

## Good

```rust
/// # Safety
///
/// `ptr` must be aligned and valid for a `u32` read.
pub unsafe fn load_word(ptr: *const u32) -> u32 {
    // SAFETY: caller promised a live, aligned `u32`.
    unsafe { ptr.read() }
}

mod words {
    pub struct Word([u8; 4]);

    impl Word {
        pub fn from_le_bytes(bytes: [u8; 4]) -> Self {
            Self(bytes)
        }

        pub fn get(&self) -> u32 {
            u32::from_le_bytes(self.0)
        }
    }
}

fn main() {
    let stored = 7u32;
    // SAFETY: `stored` is a live, aligned `u32` for this call.
    let n = unsafe { load_word(&stored) };
    assert_eq!(n, 7);
    assert_eq!(words::Word::from_le_bytes(7u32.to_le_bytes()).get(), 7);
}
```

## No Exceptions

Most rules yield when the alternative is worse. This one does not. Unsound code is never acceptable, even as a temporary shortcut, a test helper, or an internal "we would never call it that way" function. If safe callers can reach UB, the API is wrong.

## Key Points

- Soundness is judged from *other safe code*, including adversarial `Deref` / `Clone` / `Drop` impls and unusual but legal generic instantiations.
- The soundness boundary is the **module**, not the function. A safe method may rely on an invariant that another item in the *same* module established and that privacy keeps outsiders from breaking.
- Crossing a module (or crate) line without re-establishing the invariant is a new API. If that API's callers must promise something the compiler cannot check, it is `unsafe`.
- Dangerous-but-defined work stays safe (`unsafe-means-ub`). Missing a `Send` bound is not a license to implement `Send` for every `T`.

## See Also

- [unsafe-means-ub](unsafe-means-ub.md) - `unsafe` means UB risk, not "this is scary"
- [unsafe-justify-use](unsafe-justify-use.md) - even a sound block still needs a reason to exist
- [unsafe-safety-comment](unsafe-safety-comment.md) - write the contract next to every `unsafe` block
- [doc-safety-section](doc-safety-section.md) - `# Safety` on every `unsafe fn`
- [unsafe-send-sync-manual](unsafe-send-sync-manual.md) - a blanket `Send`/`Sync` impl is the usual unsound shortcut
