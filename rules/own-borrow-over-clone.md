# own-borrow-over-clone

> Borrow with `&T` and clone only to store, send across threads, or share via `Arc`

## Why It Matters

Cloning a heap-owning value (`String`, `Vec`, `HashMap`, a struct containing them) allocates and copies its contents, while borrowing is free. Not every clone is expensive: `Arc::clone`/`Rc::clone` only bump a reference count and `Copy` types are bitwise copies, so the target here is *needless deep* clones. Unnecessary clones can significantly impact performance, especially in hot paths or with large data structures.

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
        let copy = item.clone();  // N allocations!
        handle(&copy);
    }
}

// Clone just to compare or iterate
if input.clone() == expected { /* ... */ }
for item in items.clone() { process(&item); }

// Getter that forces an allocation
fn get_name(&self) -> String {
    self.name.clone()
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

// Borrow in a loop - zero allocations
fn process_all(items: &[String]) {
    for item in items {
        handle(item);  // Pass reference
    }
}

// Compare and iterate by reference
if input == expected { /* ... */ }
for item in &items { process(item); }

// Return a reference when the caller only reads
fn get_name(&self) -> &str {
    &self.name
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

// 3. Moving into a spawned task: clone the Arc handle, not the data
let shared = Arc::clone(&data);
tokio::spawn(async move { use_data(shared).await });

// 4. Copy types (no heap allocation)
let x: i32 = 42;
let y = x;  // Copy, not clone - this is fine
```

## Alternatives to Clone

| Instead of | Use |
|------------|-----|
| `s.clone()` for reading | `&s` |
| `vec.clone()` for iteration | `&vec` or `vec.iter()` |
| Clone for shared ownership | `Arc<T>` |
| Clone in a hot loop | Hoist it outside the loop |
| Clone only on some paths | `Cow` (see [own-cow-conditional](own-cow-conditional.md)) |

Clippy catches many of these:

```toml
[lints.clippy]
clone_on_copy = "warn"
clone_on_ref_ptr = "warn"
redundant_clone = "warn"
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
- [own-arc-shared](own-arc-shared.md) - Shared ownership
- [mem-clone-from](mem-clone-from.md) - Reuse allocations when cloning
- [mem-take-replace](mem-take-replace.md) - Move out of &mut without cloning
