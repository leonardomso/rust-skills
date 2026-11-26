# err-from-impl

> Implement `From<E>` for error conversions to enable `?` operator

## Why It Matters

The `?` operator automatically converts errors using `From` trait. By implementing `From<SourceError> for YourError`, you enable seamless error propagation without explicit `.map_err()` calls. This makes error handling code cleaner and ensures consistent error wrapping throughout your codebase.

## Bad

```rust
#[derive(Debug)]
enum AppError {
    Io(std::io::Error),
    Parse(serde_json::Error),
    Database(diesel::result::Error),
}

fn load_config(path: &str) -> Result<Config, AppError> {
    let content = std::fs::read_to_string(path)
        .map_err(|e| AppError::Io(e))?;  // Manual conversion everywhere
    
    let config: Config = serde_json::from_str(&content)
        .map_err(|e| AppError::Parse(e))?;  // Repeated boilerplate
    
    save_to_db(&config)
        .map_err(|e| AppError::Database(e))?;  // Gets tedious
    
    Ok(config)
}
```

## Good

```rust
#[derive(Debug)]
enum AppError {
    Io(std::io::Error),
    Parse(serde_json::Error),
    Database(diesel::result::Error),
}

// Implement From for each source error type
impl From<std::io::Error> for AppError {
    fn from(err: std::io::Error) -> Self {
        AppError::Io(err)
    }
}

impl From<serde_json::Error> for AppError {
    fn from(err: serde_json::Error) -> Self {
        AppError::Parse(err)
    }
}

impl From<diesel::result::Error> for AppError {
    fn from(err: diesel::result::Error) -> Self {
        AppError::Database(err)
    }
}

fn load_config(path: &str) -> Result<Config, AppError> {
    let content = std::fs::read_to_string(path)?;  // Auto-converts
    let config: Config = serde_json::from_str(&content)?;  // Clean!
    save_to_db(&config)?;
    Ok(config)
}
```

## Use thiserror for Automatic From

```rust
use thiserror::Error;

#[derive(Error, Debug)]
enum AppError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),  // Auto-generates From impl
    
    #[error("Parse error: {0}")]
    Parse(#[from] serde_json::Error),  // #[from] does the work
    
    #[error("Database error: {0}")]
    Database(#[from] diesel::result::Error),
}

// Now ? just works
fn load_config(path: &str) -> Result<Config, AppError> {
    let content = std::fs::read_to_string(path)?;
    let config: Config = serde_json::from_str(&content)?;
    save_to_db(&config)?;
    Ok(config)
}
```

## From with Context

Sometimes you need to add context during conversion:

```rust
use thiserror::Error;

struct Config;

#[derive(Error, Debug)]
enum ConfigError {
    #[error("failed to read config from '{path}': {source}")]
    ReadFailed {
        path: String,
        #[source]
        source: std::io::Error,
    },
}

// Can't use #[from] when you need extra context
fn load_config(path: &str) -> Result<Config, ConfigError> {
    let content = std::fs::read_to_string(path)
        .map_err(|source| ConfigError::ReadFailed {
            path: path.to_string(),
            source,
        })?;
    Ok(Config)
}

// Or use anyhow for ad-hoc context
mod with_anyhow {
    use super::Config;
    use anyhow::{Context, Result};

    fn load_config(path: &str) -> Result<Config> {
        let content = std::fs::read_to_string(path)
            .with_context(|| format!("failed to read config from '{}'", path))?;
        Ok(Config)
    }
}
```

## Blanket From Implementations

Be careful with blanket implementations:

```rust,compile_fail
use std::num::ParseIntError;

enum AppError {
    Other(String),
    Io(std::io::Error),
    Parse(ParseIntError),
}

// ❌ Too broad - conflicts with other From impls
impl<E: std::error::Error> From<E> for AppError {
    fn from(err: E) -> Self {
        AppError::Other(err.to_string())
    }
}

// Error E0119: conflicting implementations of `From<std::io::Error>`,
// because io::Error also matches the blanket impl above
impl From<std::io::Error> for AppError {
    fn from(err: std::io::Error) -> Self { AppError::Io(err) }
}
```

```rust
use std::num::ParseIntError;

enum AppError {
    Io(std::io::Error),
    Parse(ParseIntError),
}

// ✅ Specific implementations
impl From<std::io::Error> for AppError {
    fn from(err: std::io::Error) -> Self { AppError::Io(err) }
}
impl From<ParseIntError> for AppError {
    fn from(err: ParseIntError) -> Self { AppError::Parse(err) }
}
```

## See Also

- [err-thiserror-lib](./err-thiserror-lib.md) - Using thiserror for libraries
- [err-source-chain](./err-source-chain.md) - Preserving error chains
- [err-question-mark](./err-question-mark.md) - The ? operator
- [conv-tryfrom-fallible](./conv-tryfrom-fallible.md) - TryFrom for fallible conversions
