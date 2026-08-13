# own-borrow-over-clone

> Prefer `&T` borrowing over `.clone()`

## Why It Matters

`Clone` means "duplicate according to this type's semantics." A `String` or
owned object graph may allocate and copy data; an `Arc` clone updates a
reference count; some clones are small inline copies. Borrowing avoids creating
a second owned value and usually avoids that work, but it also constrains
lifetimes and mutation. Borrow when the callee only needs access, and clone
when independent ownership is part of the contract.

## Bad

```rust
fn process(data: &String) {
    let local = data.clone();  // Unnecessary allocation!
    println!("{}", local);
}

fn count_words(text: &String) -> usize {
    let owned = text.clone();  // Why clone just to read?
    owned.split_whitespace().count()
}

// Clone in a loop - multiplied cost
fn process_all(items: &[String]) {
    for item in items {
        let copy = item.clone();  // Up to N independent String allocations.
        handle(&copy);
    }
}
```

## Good

```rust
fn process(data: &str) {  // Accept &str, more flexible
    println!("{}", data);  // No allocation needed
}

fn count_words(text: &str) -> usize {
    text.split_whitespace().count()  // Just borrow
}

// Borrow in a loop - no ownership duplication
fn process_all(items: &[String]) {
    for item in items {
        handle(item);  // Pass reference
    }
}
```

## When Clone Is Acceptable

```rust
// 1. Need owned data for storage
struct Cache {
    data: HashMap<String, String>,
}

impl Cache {
    fn insert(&mut self, key: &str, value: &str) {
        // Clone needed - we're storing owned data
        self.data.insert(key.to_string(), value.to_string());
    }
}

// 2. Need to send across threads
fn spawn_worker(data: &Config) {
    let owned = data.clone();  // Clone needed for 'static
    std::thread::spawn(move || {
        use_config(owned);
    });
}

// 3. Copy types (no heap allocation)
let x: i32 = 42;
let y = x;  // Copy, not clone - this is fine
```

## Evidence

From ripgrep's codebase - uses `Cow` to avoid clones:
```rust
// https://github.com/BurntSushi/ripgrep/blob/master/crates/globset/src/pathutil.rs
pub(crate) fn file_name<'a>(path: &Cow<'a, [u8]>) -> Option<Cow<'a, [u8]>> {
    match *path {
        Cow::Borrowed(path) => Cow::Borrowed(&path[last_slash..]),
        Cow::Owned(ref path) => Cow::Owned(path.clone()),
    }
}
```

## See Also

- [own-slice-over-vec](own-slice-over-vec.md) - Accept slices instead of references to collections
- [own-cow-conditional](own-cow-conditional.md) - Use Cow for conditional ownership
- [mem-clone-from](mem-clone-from.md) - Reuse allocations when cloning
- [mem-take-replace](mem-take-replace.md) - Move out of &mut without cloning
