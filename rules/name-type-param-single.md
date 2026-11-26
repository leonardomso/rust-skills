# name-type-param-single

> Use single uppercase letters for type parameters: `T`, `E`, `K`, `V`

## Why It Matters

Generic type parameters conventionally use single uppercase letters. This keeps signatures concise and follows established conventions that readers instantly recognize. `T` for "type", `E` for "error", `K` for "key", `V` for "value" are universal in Rust.

## Bad

```rust
// Verbose type parameters
struct Container<ElementType> {
    items: Vec<ElementType>,
}

fn process<InputType, OutputType>(input: InputType) -> OutputType { ... }

// Lowercase - looks like lifetime
struct Wrapper<t> { ... }  // Confusing
```

## Good

```rust
// Single uppercase letters
struct Container<T> {
    items: Vec<T>,
}

fn process<I, O: Default>(input: I) -> O {
    let _ = input;
    O::default()
}

// Standard conventions
struct HashMap<K, V> { entries: Vec<(K, V)> }  // K=Key, V=Value
enum Result<T, E> { Ok(T), Err(E) }             // T=Type, E=Error
enum Option<T> { Some(T), None }                // T=Type
struct Ref<'a, T> { value: &'a T }              // Lifetime + Type
```

## Standard Type Parameter Names

| Parameter | Meaning | Example |
|-----------|---------|---------|
| `T` | Type (generic) | `Vec<T>` |
| `E` | Error | `Result<T, E>` |
| `K` | Key | `HashMap<K, V>` |
| `V` | Value | `HashMap<K, V>` |
| `I` | Input / Item | `Iterator<Item = I>` |
| `O` | Output | `Fn(I) -> O` |
| `R` | Return / Result | `fn() -> R` |
| `S` | State | `StateMachine<S>` |
| `A` | Allocator | `Vec<T, A>` |
| `F` | Function | `map<F>(f: F)` |

## Multiple Type Parameters

```rust
use std::error::Error;

trait Input {}
trait Output {}

// Use related letters
fn transform<I, O, E>(input: I) -> Result<O, E>
where
    I: Input,
    O: Output,
    E: Error,
{
    let _ = input;
    unimplemented!()
}

// Or sequential: T, U, V
fn combine<T, U, V: Default>(a: T, b: U) -> V {
    let _ = (a, b);
    V::default()
}

// Descriptive only when many parameters need clarity
struct Query<Db, Row, Err> {
    db: Db,
    rows: Vec<Row>,
    error: Option<Err>,
}
```

## Trait Bounds

```rust
use std::error::Error;
use std::fmt::Debug;
use std::io::Error as IoError;

// Keep type params short, move complexity to where clause
fn process_where<T, E>(value: T) -> Result<T, E>
where
    T: Clone + Debug + Send + Sync,
    E: Error + From<IoError>,
{
    Ok(value)
}

// Not inline: the bounds crowd out the signature. Too long!
fn process_inline<T: Clone + Debug + Send + Sync, E: Error + From<IoError>>(value: T) -> Result<T, E> {
    Ok(value)
}
```

## See Also

- [name-lifetime-short](./name-lifetime-short.md) - Lifetime parameter naming
- [name-types-camel](./name-types-camel.md) - Concrete type naming
- [type-generic-bounds](./type-generic-bounds.md) - Trait bounds
