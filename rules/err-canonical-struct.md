# err-canonical-struct

> Keep extensible library errors opaque, preserve `source()`, and expose only stable recovery queries

## Why It Matters

A public enum makes every variant part of the compatibility contract. That is
appropriate when callers must exhaustively handle a closed domain, but it is a
poor fit for an evolving library boundary with internal and upstream failure
modes. An opaque, situation-specific struct can add internal causes without a
breaking change while still participating in Rust's standard error chain.

Opacity must not discard interoperability. `Display` provides concise context;
`Error::source()` exposes the underlying cause to reporters and downcasting;
`Debug` or the application reporter decides whether to include the complete
chain and backtrace.

## Bad

```rust
#[derive(Debug)]
pub enum GlobalError {
    Io(std::io::Error),
    Protocol,
    Configuration,
}

impl std::fmt::Display for GlobalError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        // Embedding every cause and backtrace here makes normal messages noisy
        // and duplicates output from reporters that walk source().
        write!(f, "{self:?}")
    }
}

impl std::error::Error for GlobalError {}
```

## Good

```rust
use std::error::Error as StdError;
use std::fmt::{Display, Formatter};
use std::path::{Path, PathBuf};

#[derive(Debug)]
enum ConfigurationErrorKind {
    Io(std::io::Error),
    InvalidSyntax,
}

#[derive(Debug)]
pub struct ConfigurationError {
    file: PathBuf,
    kind: ConfigurationErrorKind,
}

impl ConfigurationError {
    pub(crate) fn io(file: PathBuf, error: std::io::Error) -> Self {
        Self {
            file,
            kind: ConfigurationErrorKind::Io(error),
        }
    }

    pub fn file(&self) -> &Path {
        &self.file
    }

    pub fn is_invalid_syntax(&self) -> bool {
        matches!(self.kind, ConfigurationErrorKind::InvalidSyntax)
    }
}

impl Display for ConfigurationError {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        write!(f, "failed to load configuration from {}", self.file.display())
    }
}

impl StdError for ConfigurationError {
    fn source(&self) -> Option<&(dyn StdError + 'static)> {
        match &self.kind {
            ConfigurationErrorKind::Io(error) => Some(error),
            ConfigurationErrorKind::InvalidSyntax => None,
        }
    }
}

fn main() {
    let error = ConfigurationError::io(
        PathBuf::from("settings.toml"),
        std::io::Error::other("unavailable"),
    );
    assert_eq!(error.to_string(), "failed to load configuration from settings.toml");
    assert!(error.source().is_some());
}
```

## Choosing the Public Shape

- Use a public enum for a deliberately closed domain whose variants are the
  recovery protocol.
- Use an opaque struct when internal causes may evolve independently of caller
  recovery behavior.
- Split unrelated situations into separate error types; do not create one
  crate-wide catch-all merely to standardize a name.
- Expose stable queries such as `is_not_found()` or typed context accessors.
  Do not mirror every private kind with a public boolean.

## Error and Backtrace Contract

- Keep `Display` concise and single-line unless the surrounding API explicitly
  defines another format.
- Return the immediate underlying error from `source()`. Generic reporters own
  traversal and presentation of the chain.
- Capture a backtrace only when the application error strategy does not already
  provide one and operational evidence justifies the per-error cost. Keep its
  rendering out of `Display`.
- Use `From` when conversion preserves enough context; use `map_err` or a
  constructor when the operation, resource, or identifier must be attached.
- Redact credentials, tokens, and sensitive user data from every representation.

## See Also

- [err-custom-type](err-custom-type.md) - public enums for closed recovery protocols
- [err-source-chain](err-source-chain.md) - preserve standard cause traversal
- [err-context-chain](err-context-chain.md) - attach operation context at boundaries
- [err-from-impl](err-from-impl.md) - owned conversions for `?`
- [err-thiserror-lib](err-thiserror-lib.md) - derive boilerplate without exposing internals
- [obs-no-sensitive-data](obs-no-sensitive-data.md) - redact diagnostics
