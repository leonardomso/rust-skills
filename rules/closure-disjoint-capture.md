# closure-disjoint-capture

> Capture only what you use; lean on edition-2021 disjoint closure captures

## Why It Matters

Before the 2021 edition, a closure captured entire variables — using `config.threshold` pulled in the whole `config` struct, preventing other code from using any other field of `config` concurrently. Since Rust 2021, closures capture individual fields (`config.threshold` only), so sibling fields remain independently accessible. This holds for `move` closures too. A closure still captures the whole variable when it uses the variable as a whole, for example by calling a `&self` method on it or by passing it to a function. Take advantage of this: write closures that reference only the specific fields or values they need, and add `move` only when ownership is genuinely required. When you do need to `move` a single field, bind it to a local first so the rest of the struct stays usable.

## Bad

```rust
struct Config {
    threshold: i32,
    label: String,
}

impl Config {
    fn is_enabled(&self) -> bool {
        self.threshold > 0
    }
}

fn demo_bad() {
    let mut config = Config { threshold: 10, label: String::from("demo") };

    // Calling a method inside the closure uses `config` as a whole, so the
    // closure borrows the entire struct, not just `threshold`.
    let check = || config.is_enabled();

    // error[E0502]: cannot borrow `config.label` as mutable
    // config.label.push('!');
    assert!(check());
}
```

## Good

```rust
struct Config {
    threshold: i32,
    label: String,
}

fn demo_good() {
    let mut config = Config { threshold: 10, label: String::from("active") };

    // Edition 2021: the closure captures only `config.threshold`.
    // `config.label` is NOT captured, so it can even be mutated meanwhile.
    let check = || config.threshold > 0;

    config.label.push('!'); // fine: disjoint from `config.threshold`
    println!("label: {}", config.label);
    assert!(check());
}

// When you need `move` for one field, bind it first.
fn make_checker(config: Config) -> (impl Fn() -> bool, String) {
    // Bind the field to a local, then move only that local into the closure.
    let threshold = config.threshold;
    let checker = move || threshold > 0; // moves `threshold` (i32, Copy), not `config`

    // `config.label` is still available here.
    (checker, config.label)
}

fn demo_bind_first() {
    let cfg = Config { threshold: 5, label: String::from("info") };
    let (check, label) = make_checker(cfg);
    println!("label returned: {label}");
    assert!(check());
}
```

## Key Points

- **Edition 2021 rule:** closures capture the *minimal* path used — `foo.bar` rather than `foo`. This reduces spurious borrow conflicts.
- **`move` is disjoint too.** `move || config.tags.len()` moves only `config.tags`; the other fields stay usable. Capture widens to the whole variable when the closure uses it whole (`config.method()`, `&config`), when it goes through a reference (`move || self.field` with `&self` captures the reference), or when the type implements `Drop` (you cannot move a field out of it).
- **`if let` captures (Rust 1.100):** closures now capture variables used in `if let` more precisely. This can surface new borrow errors after an upgrade. Check which fields the pattern really reads.
- **Copy types** (integers, booleans) are copied into the closure rather than moved, so the original remains valid even with `move`.
- **Borrow by reference first:** only escalate to `move` when the closure must outlive the scope (see [closure-move-capture](closure-move-capture.md)).

## See Also

- [own-borrow-over-clone](own-borrow-over-clone.md) - prefer borrowing over cloning
- [closure-move-capture](closure-move-capture.md) - when to use `move` and how to clone selectively
