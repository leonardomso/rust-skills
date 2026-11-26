# own-cow-conditional

> Use `Cow<'a, T>` for conditional ownership

## Why It Matters

`Cow` (Clone-on-Write) lets you avoid allocations when you *might* need to own data but usually don't. It holds either a borrowed reference or an owned value, cloning only when mutation is needed.

## Bad

```rust
// Always allocates, even when input doesn't need modification
fn normalize_path(path: &str) -> String {
    if path.contains("//") {
        path.replace("//", "/")  // Allocation needed
    } else {
        path.to_string()  // Unnecessary allocation!
    }
}

// Always clones the error message
fn format_error(code: u32) -> String {
    match code {
        404 => "Not Found".to_string(),      // Unnecessary!
        500 => "Internal Error".to_string(), // Unnecessary!
        _ => format!("Error {}", code),      // This one needs allocation
    }
}
```

## Good

```rust
use std::borrow::Cow;

// Only allocates when needed
fn normalize_path(path: &str) -> Cow<'_, str> {
    if path.contains("//") {
        Cow::Owned(path.replace("//", "/"))  // Allocate
    } else {
        Cow::Borrowed(path)  // Zero-cost borrow
    }
}

// Static strings stay borrowed
fn format_error(code: u32) -> Cow<'static, str> {
    match code {
        404 => Cow::Borrowed("Not Found"),      // No allocation
        500 => Cow::Borrowed("Internal Error"), // No allocation
        _ => Cow::Owned(format!("Error {}", code)), // Allocate only for unknown
    }
}
```

## Real-World Example from ripgrep

```rust
// https://github.com/BurntSushi/ripgrep/blob/master/crates/globset/src/pathutil.rs
pub(crate) fn file_name<'a>(path: &Cow<'a, [u8]>) -> Option<Cow<'a, [u8]>> {
    let last_slash = path.rfind_byte(b'/').map(|i| i + 1).unwrap_or(0);
    match *path {
        Cow::Borrowed(path) => Some(Cow::Borrowed(&path[last_slash..])),
        Cow::Owned(ref path) => {
            let mut path = path.clone();
            path.drain_bytes(..last_slash);
            Some(Cow::Owned(path))
        }
    }
}
```

## Clone-on-Write Pattern

Two methods turn a `Cow` into something you can change, and they do different things:

- `to_mut(&mut self) -> &mut B::Owned` keeps the `Cow`. If it is `Borrowed`, it clones the data into `Owned` once and returns a mutable reference. If it is already `Owned`, it just returns the reference.
- `into_owned(self) -> B::Owned` consumes the `Cow` and returns the owned value. It clones if `Borrowed` and moves if `Owned`.

```rust
use std::borrow::Cow;

// to_mut: mutate in place, converting to Owned only when needed
fn censor(mut text: Cow<'_, str>) -> Cow<'_, str> {
    if text.contains("bad_word") {
        let s = text.to_mut(); // clones only if `text` was Borrowed
        *s = s.replace("bad_word", "***");
    }
    text // unchanged input passes through still Borrowed
}

// into_owned: you need a plain String at the end regardless
fn into_message(text: Cow<'_, str>) -> String {
    text.into_owned() // moves if Owned, clones if Borrowed
}

fn demo() {
    let clean = censor(Cow::Borrowed("hello world"));
    assert!(matches!(clean, Cow::Borrowed(_))); // no allocation on this path

    let dirty = censor(Cow::Borrowed("hello bad_word"));
    assert_eq!(dirty, "hello ***"); // allocated only here
    let _owned: String = into_message(dirty);
}
```

`Cow` removes allocations on the paths that leave data unchanged. It does not make the changing path free, so measure if a hot path changes most of its inputs.

## Cow with Collections

```rust
use std::borrow::Cow;

// Mixed borrowed/owned in a collection
fn collect_errors<'a>(
    static_errors: &[&'static str],
    dynamic_errors: Vec<String>,
) -> Vec<Cow<'a, str>> {
    let mut errors: Vec<Cow<str>> = Vec::new();
    
    // Static strings - no allocation
    for &e in static_errors {
        errors.push(Cow::Borrowed(e));
    }
    
    // Dynamic strings - take ownership
    for e in dynamic_errors {
        errors.push(Cow::Owned(e));
    }
    
    errors
}
```

## When to Use Cow

| Situation | Use Cow? |
|-----------|----------|
| Usually borrow, sometimes own | Yes |
| Always need owned data | No, just use owned type |
| Always borrow | No, just use reference |
| Hot path, avoiding all allocations | Yes |
| Returning static strings or formatted | Yes |

## See Also

- [own-borrow-over-clone](own-borrow-over-clone.md) - Prefer borrowing over cloning
- [mem-avoid-format](mem-avoid-format.md) - Avoid format! when possible
