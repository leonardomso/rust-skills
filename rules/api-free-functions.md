# api-free-functions

> Put construction on the type; put computation with no receiver at module scope

## Why It Matters

Rust functions do not need a type to live on. `Decoder::validate_shape(rows, cols)` forces every caller to name a type that is not an argument and is not returned. Inherent associated functions are for creating a value (`new`, `with_capacity`, `from_parts`). Work that has no `self` and does not produce `Self` belongs next to the type as a module-level function. Methods with a receiver stay on the type.

This is the opposite pressure from `api-inherent-core`: essential *instance* behavior remains inherent so rustdoc and completion show it. Do not "clean up" `decode(&self)` into a free function.

## Bad

```rust
struct Decoder {
    width: usize,
}

impl Decoder {
    fn new(width: usize) -> Self {
        Self { width }
    }

    fn decode(&self, bytes: &[u8]) -> usize {
        self.width.min(bytes.len())
    }

    // No receiver, does not build a `Decoder` — does not belong here.
    fn validate_shape(rows: usize, cols: usize) -> bool {
        rows > 0 && cols > 0
    }
}

fn main() {
    let _ok = Decoder::validate_shape(2, 4);
}
```

## Good

```rust
struct Decoder {
    width: usize,
}

impl Decoder {
    fn new(width: usize) -> Self {
        Self { width }
    }

    fn decode(&self, bytes: &[u8]) -> usize {
        self.width.min(bytes.len())
    }
}

fn validate_shape(rows: usize, cols: usize) -> bool {
    rows > 0 && cols > 0
}

fn main() {
    let decoder = Decoder::new(4);
    assert!(validate_shape(2, 4));
    assert_eq!(decoder.decode(b"payload"), 4);
}
```

## Trait Associated Functions

Associated functions on **traits** are normal Rust, including constructors that implementers provide:

```rust
struct Foo;

impl Default for Foo {
    fn default() -> Self {
        Self
    }
}

fn main() {
    let _ = Foo::default();
}
```

`Default::default`, `From::from`, and `Clone::clone` stay on the trait. The rule targets inherent `impl Type { fn helper() }` blocks used as a namespace.

## Key Points

- Associated functions primarily **create** `Self`.
- General computation with no receiver is a **free function** at module scope.
- Methods (`&self` / `&mut self` / `self`) stay on the type.
- Trait associated functions are not a smell.
- If the function *is* the type's reason to exist, keep it inherent and forward from any trait (`api-inherent-core`).

## See Also

- [api-inherent-core](api-inherent-core.md) - core receiver behavior stays on the type; traits forward
- [api-default-impl](api-default-impl.md) - `Default::default` is the usual associated constructor trait
- [api-builder-pattern](api-builder-pattern.md) - repeated or optional construction is `Foo::builder()`, not a free `build_foo`
- [name-funcs-snake](name-funcs-snake.md) - free functions still follow `snake_case`
