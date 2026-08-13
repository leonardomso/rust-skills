# doc-examples-section

> Include `# Examples` with runnable code

## Why It Matters

Examples show users how the API fits together. Runnable doctests compile and,
unless marked `no_run`, execute with the crate's test suite. `ignore`,
`compile_fail`, target cfgs, and external-service setup have different
contracts; do not claim an example is continuously verified when CI skips it.

Keep short, copyable calls in rustdoc. Put complete workflows that need setup,
multiple modules, or external services under the repository's `examples/`
directory and compile them in CI. Users and coding agents need both: a local
answer beside the item and an end-to-end program they can run.

## Bad

```rust
/// Parses a string into a Foo.
pub fn parse(s: &str) -> Result<Foo, Error> {
    // No examples - users have to guess usage
}

/// A widget for doing things.
/// 
/// This widget is very useful.
pub struct Widget {
    // Still no examples
}
```

## Good

```rust
/// Parses a string into a Foo.
///
/// # Examples
///
/// ```
/// # fn main() -> Result<(), Box<dyn std::error::Error>> {
/// use my_crate::parse;
///
/// let foo = parse("hello")?;
/// assert_eq!(foo.name(), "hello");
/// # Ok(())
/// # }
/// ```
///
/// Handles empty strings:
///
/// ```
/// # fn main() -> Result<(), Box<dyn std::error::Error>> {
/// use my_crate::parse;
///
/// let foo = parse("")?;
/// assert!(foo.is_empty());
/// # Ok(())
/// # }
/// ```
pub fn parse(s: &str) -> Result<Foo, Error> {
    // ...
}
```

## Use ? Not unwrap()

```rust
/// Loads configuration from a file.
///
/// # Examples
///
/// ```
/// # fn main() -> Result<(), Box<dyn std::error::Error>> {
/// use my_crate::Config;
///
/// let config = Config::load("config.toml")?;
/// println!("Port: {}", config.port);
/// # Ok(())
/// # }
/// ```
pub fn load(path: &str) -> Result<Config, Error> {
    // ...
}
```

## Hide Setup Code

```rust
/// Processes items from a database.
///
/// # Examples
///
/// ```
/// # use my_crate::{Database, Item};
/// # fn get_db() -> Database { Database::mock() }
/// let db = get_db();
/// let items = db.process_items()?;
/// assert!(!items.is_empty());
/// # Ok::<(), my_crate::Error>(())
/// ```
pub fn process_items(&self) -> Result<Vec<Item>, Error> {
    // ...
}
```

## Multiple Examples

```rust
/// Creates a new buffer with the specified capacity.
///
/// # Examples
///
/// Basic usage:
///
/// ```
/// use my_crate::Buffer;
///
/// let buf = Buffer::with_capacity(1024);
/// assert_eq!(buf.capacity(), 1024);
/// ```
///
/// Zero capacity creates an empty buffer:
///
/// ```
/// use my_crate::Buffer;
///
/// let buf = Buffer::with_capacity(0);
/// assert!(buf.is_empty());
/// ```
pub fn with_capacity(cap: usize) -> Self {
    // ...
}
```

## Show Error Cases

```rust
/// Divides two numbers.
///
/// # Examples
///
/// ```
/// use my_crate::divide;
///
/// assert_eq!(divide(10, 2), Ok(5));
/// ```
///
/// Division by zero returns an error:
///
/// ```
/// use my_crate::{divide, MathError};
///
/// assert_eq!(divide(10, 0), Err(MathError::DivisionByZero));
/// ```
pub fn divide(a: i32, b: i32) -> Result<i32, MathError> {
    // ...
}
```

## Running Doc Tests

```bash
# Run all doc tests
cargo test --doc

# Run doc tests for specific item
cargo test --doc my_function
```

## See Also

- [doc-question-mark](doc-question-mark.md) - Use ? in examples
- [doc-hidden-setup](doc-hidden-setup.md) - Hide setup code with #
- [doc-errors-section](doc-errors-section.md) - Document error conditions
