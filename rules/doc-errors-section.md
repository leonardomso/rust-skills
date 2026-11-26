# doc-errors-section

> Give every fallible public function an `# Errors` section that lists each failure condition and links the error variants

## Why It Matters

Functions returning `Result` can fail in specific, documented ways. The `# Errors` section tells users exactly when and why a function might return an error, enabling them to handle failures appropriately without reading source code.

This is especially critical for library code where users cannot easily inspect implementation details.

## Bad

```rust
/// Opens a file and reads its contents.
pub fn read_file(path: &Path) -> Result<String, Error> {
    // Users have no idea what errors to expect
}

/// Connects to the database.
pub async fn connect(url: &str) -> Result<Connection, DbError> {
    // Multiple failure modes, none documented
}
```

## Good

```rust
/// Opens a file and reads its contents as a UTF-8 string.
///
/// # Errors
///
/// Returns an error if:
/// - The file does not exist ([`Error::NotFound`])
/// - The process lacks permission to read the file ([`Error::PermissionDenied`])
/// - The file contains invalid UTF-8 ([`Error::InvalidUtf8`])
pub fn read_file(path: &Path) -> Result<String, Error> {
    // ...
}

/// Establishes a connection to the database.
///
/// # Errors
///
/// This function will return an error if:
/// - The URL is malformed ([`DbError::InvalidUrl`])
/// - The database server is unreachable ([`DbError::ConnectionFailed`])
/// - Authentication fails ([`DbError::AuthenticationFailed`])
/// - The connection pool is exhausted ([`DbError::PoolExhausted`])
pub async fn connect(url: &str) -> Result<Connection, DbError> {
    // ...
}
```

## Error Documentation Patterns

### Simple Single Error

```rust
/// Parses a string as an integer.
///
/// # Errors
///
/// Returns [`ParseIntError`] if the string is not a valid integer.
pub fn parse_int(s: &str) -> Result<i64, ParseIntError> {
    s.parse()
}
```

### Multiple Error Variants

```rust
/// Sends an HTTP request and returns the response.
///
/// # Errors
///
/// | Error | Condition |
/// |-------|-----------|
/// | [`HttpError::Timeout`] | Request exceeded timeout duration |
/// | [`HttpError::InvalidUrl`] | URL could not be parsed |
/// | [`HttpError::ConnectionRefused`] | Server refused connection |
/// | [`HttpError::TlsError`] | TLS handshake failed |
pub fn send(request: Request) -> Result<Response, HttpError> {
    // ...
}
```

### Propagated Errors

```rust
/// Loads configuration from a file.
///
/// # Errors
///
/// Returns an error if:
/// - The configuration file cannot be read (IO error)
/// - The file contains invalid TOML syntax
/// - Required fields are missing from the configuration
///
/// The underlying error is wrapped with context about which
/// configuration file failed to load.
pub fn load_config(path: &Path) -> Result<Config, anyhow::Error> {
    // ...
}
```

## Linking to Error Types

Use intra-doc links to connect error variants to their definitions. Pick the style that fits: a bullet list for several conditions, a table or `Returns [..] if` lines when mapping to variants, prose for complex conditions.

```rust
/// # Errors
///
/// Returns [`ValidationError::TooShort`] if the input is less than
/// the minimum length, or [`ValidationError::InvalidChars`] if it
/// contains forbidden characters.
```

## Errors vs Panics

Document both when a function can fail and panic. `# Errors` covers `Err` returns; `# Panics` covers caller bugs.

```rust
/// Divides two numbers.
///
/// # Errors
///
/// Returns [`MathError::DivisionByZero`] if `divisor` is zero.
///
/// # Panics
///
/// Panics if `dividend` is `i64::MIN` and `divisor` is `-1` (overflow).
pub fn divide(dividend: i64, divisor: i64) -> Result<i64, MathError> {
    // ...
}
```

## Clippy Lint

```toml
# Cargo.toml - warn when a public fallible fn has no # Errors section
[lints.clippy]
missing_errors_doc = "warn"
```

## See Also

- [doc-panics-section](./doc-panics-section.md) - Documenting panics
- [doc-intra-links](./doc-intra-links.md) - Linking to types
- [doc-examples-section](./doc-examples-section.md) - Examples in documentation
- [err-thiserror-lib](./err-thiserror-lib.md) - Defining error types
