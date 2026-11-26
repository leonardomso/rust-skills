# doc-intra-links

> Link types, methods, and modules in doc comments with intra-doc links such as [`Type`] and [`Self::method`]

## Why It Matters

Intra-doc links (`[TypeName]`, `[method](Self::method)`) create clickable references in generated documentation. They're verified at doc-build time, catching broken links early. Unlike URL links or plain-text names, they stay clickable and update when items are renamed or moved.

## Bad

```rust
/// Returns the length of the buffer.
/// 
/// See also `capacity()` for the allocated size, and the
/// `Buffer` struct for more details.
pub fn len(&self) -> usize {
    self.data.len()
}

/// Parses the input using std::str::FromStr trait.
/// Check the Error enum for possible failures.
pub fn parse<T: FromStr>(input: &str) -> Result<T, Error> {
    // ...
}
```

## Good

```rust
/// Returns the length of the buffer.
/// 
/// See also [`capacity()`](Self::capacity) for the allocated size, and
/// [`Buffer`] for more details.
pub fn len(&self) -> usize {
    self.data.len()
}

/// Parses the input using [`FromStr`] trait.
/// Check [`Error`] for possible failures.
///
/// [`FromStr`]: std::str::FromStr
pub fn parse<T: FromStr>(input: &str) -> Result<T, Error> {
    // ...
}
```

## Link Syntax

| Syntax | Links To | Example |
|--------|----------|---------|
| `[Name]` | Item in scope | `[Vec]`, `[Option]` |
| `[path::Name]` | Fully qualified item | `[std::vec::Vec]`, `[crate::utils::helper]` |
| `[super::Name]` | Item in parent module | `[super::Parent]` |
| `[module]` | Module in scope | `[parser]` |
| `[Self::method]` | Method on current type | `[Self::new]` |
| `[Type::method]` | Method on other type | `[String::new]` |
| `[Type::CONST]` | Associated constant | `[usize::MAX]` |
| `[text](path)` | Custom text | `[see here](Self::len)` |

## Common Patterns

### Linking to Self Members

```rust
impl Buffer {
    /// Creates an empty buffer.
    ///
    /// Use [`with_capacity`](Self::with_capacity) if you know the size.
    pub fn new() -> Self { /* ... */ }
    
    /// Creates a buffer with pre-allocated capacity.
    ///
    /// See [`new`](Self::new) for the default constructor.
    pub fn with_capacity(cap: usize) -> Self { /* ... */ }
}
```

### Linking to Trait Methods

```rust
/// Implements [`Iterator`]; [`Iterator::next`] advances the cursor.
pub struct MyIterator { /* ... */ }
```

### Linking to Errors and Related Items

```rust
/// Parses input and returns a [`ParseResult`].
///
/// # Errors
///
/// Returns [`ParseError::InvalidSyntax`] if the input contains invalid tokens.
///
/// See also [`Tokenizer`], the tokenizer this parser uses, and [`parse_file`].
pub fn parse(input: &str) -> ParseResult { /* ... */ }
```

### Disambiguation

When names conflict, use suffixes:

```rust
/// See [`foo()`](fn@foo) for the function and [`foo`](mod@foo) for the module.

/// Works with [`Error`](struct@Error) struct or [`Error`](trait@Error) trait.
```

| Suffix | Item Type |
|--------|-----------|
| `fn@` | Function |
| `mod@` | Module |
| `struct@` | Struct |
| `enum@` | Enum |
| `trait@` | Trait |
| `type@` | Type alias |
| `const@` | Constant |
| `macro@` | Macro |

### Reference-Style Links

For repeated links or long paths:

```rust
/// Parses using [`serde`] with [`Deserialize`] trait.
/// Returns a [`Result`] that may contain [`Error`].
///
/// [`serde`]: https://serde.rs
/// [`Deserialize`]: serde::Deserialize
/// [`Result`]: std::result::Result
/// [`Error`]: crate::Error
```

## Verification

Enable link checking in CI:

```bash
CARGO_BUILD_WARNINGS=deny cargo doc --no-deps
```

This fails if any intra-doc links are broken. `build.warnings` (stable since Rust 1.97) only affects your own packages, unlike `RUSTDOCFLAGS="-D warnings"`, which also applies to the documentation of every dependency. See [lint-build-warnings](lint-build-warnings.md). To deny it in the crate itself:

```toml
[lints.rustdoc]
broken_intra_doc_links = "deny"
```

## Other Rustdoc Lints Worth Keeping On

| Lint | Since | What it reports |
|------|-------|-----------------|
| `rustdoc::broken_intra_doc_links` | warn by default | Link that does not resolve |
| `rustdoc::invalid_markdown_table` | Rust 1.100 | Unescaped `\|` in a table cell, so the rest of the row is dropped |
| `rustdoc::unused_footnote_definition` | Rust 1.99 | `[^1]: ...` that nothing references |

```rust
//! | closure |
//! | ------- |
//! | `code_with(\|arg\| arg)` |  // escape pipes inside table cells
```

## See Also

- [doc-all-public](./doc-all-public.md) - Documenting public items
- [doc-examples-section](./doc-examples-section.md) - Adding examples
- [doc-errors-section](./doc-errors-section.md) - Documenting errors
- [lint-deny-correctness](./lint-deny-correctness.md) - Lint settings
