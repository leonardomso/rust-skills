# err-result-over-panic

> Return `Result<T, E>` instead of panicking for recoverable errors

## Why It Matters

Panics unwind the stack and crash the thread—or the process when the caller
uses `panic = "abort"`. `Result<T, E>` is for conditions the caller can
reasonably encounter and act on: retry, fallback, correct input, propagate, or
log. A detected programming bug or documented contract violation is different:
there is no useful runtime recovery value, so it should panic rather than
inventing an error variant that callers cannot handle.

## Bad

```rust
fn parse_config(path: &str) -> Config {
    let content = std::fs::read_to_string(path)
        .expect("Failed to read config");  // Crashes on missing file
    
    serde_json::from_str(&content)
        .expect("Invalid config format")   // Crashes on bad JSON
}

fn divide(a: i32, b: i32) -> i32 {
    if b == 0 {
        panic!("Division by zero!");  // Crashes the program
    }
    a / b
}
```

Caller has no chance to recover or provide a fallback.

## Good

```rust
use thiserror::Error;

#[derive(Error, Debug)]
enum ConfigError {
    #[error("Failed to read config file: {0}")]
    Io(#[from] std::io::Error),
    #[error("Invalid config format: {0}")]
    Parse(#[from] serde_json::Error),
}

fn parse_config(path: &str) -> Result<Config, ConfigError> {
    let content = std::fs::read_to_string(path)?;
    let config = serde_json::from_str(&content)?;
    Ok(config)
}

fn divide(a: i32, b: i32) -> Result<i32, &'static str> {
    if b == 0 {
        return Err("Division by zero");
    }
    Ok(a / b)
}

// Caller decides how to handle
match parse_config("app.json") {
    Ok(config) => run_app(config),
    Err(e) => {
        eprintln!("Using default config: {}", e);
        run_app(Config::default())
    }
}
```

## When Panic IS Appropriate

```rust
// 1. Bug in the program (invariant violation)
fn get_cached_value(&self, key: &str) -> &Value {
    self.cache.get(key).expect("BUG: key was verified to exist")
}

// 2. A documented precondition was violated.
fn page_at(pages: &[Page], index: usize) -> &Page {
    assert!(index < pages.len(), "page index {index} out of bounds");
    &pages[index]
}

// 3. Setup/initialization whose failure terminates this application
fn main() {
    let config = Config::load().expect("Failed to load required config");
    // This is application policy, not a reusable library API.
}

// 4. Tests
#[test]
fn test_parse() {
    let result = parse("valid input").unwrap(); // unwrap OK in tests
    assert_eq!(result, expected);
}

// 5. Examples and prototypes
fn main() {
    // Quick prototype, panic is fine
    let data = fetch_data().unwrap();
}
```

## Panic vs Result Decision Guide

| Situation | Use |
|-----------|-----|
| File not found | `Result` |
| Network error | `Result` |
| Invalid user input | `Result` |
| Parse error | `Result` |
| Index out of bounds (from user data) | `Result` |
| Index out of bounds (internal bug) | Panic |
| Violated internal invariant | Panic |
| Violated safe API precondition | Prefer a type/`Result`; panic only when the API deliberately specifies it |
| Unimplemented production path | Do not ship it |
| State proved unreachable by a maintained invariant | Panic with the invariant; never use unchecked UB as an assertion |

You do not need to add an expensive check merely to detect every possible
contract violation. Omitting a check may produce an unspecified but defined
result; it must never make a safe API undefined. Methods whose contract
explicitly requests a panic, such as an `unwrap`-style accessor, are also
allowed.

Code must remain minimally panic-safe even when the design treats panic as
termination: if an unwind is caught by a host, destructors and later safe code
must not observe memory unsafety or broken validity invariants. Const evaluation
may use assertions or unwrap-like operations to reject an invalid constant at
compile time.

## Library Versus Application Boundary

```rust
// Library: return a typed rejection for input-controlled failure.
pub fn parse(input: &str) -> Result<Ast, ParseError> {
    // ...
}

// Application: map startup failure to diagnostics and controlled termination.
fn main() -> std::process::ExitCode {
    if let Err(e) = run() {
        eprintln!("startup failed: {e:#}");
        return std::process::ExitCode::FAILURE;
    }
    std::process::ExitCode::SUCCESS
}
```

Returning a failure exit status is not a panic. Keep sensitive configuration
and credentials out of the rendered chain, and flush telemetry only within a
bounded shutdown budget.

## See Also

- [err-thiserror-lib](./err-thiserror-lib.md) - Define error types for libraries
- [err-anyhow-app](./err-anyhow-app.md) - Ergonomic errors for applications
- [err-no-unwrap-prod](./err-no-unwrap-prod.md) - Avoid unwrap in production code
- [anti-unwrap-abuse](./anti-unwrap-abuse.md) - When unwrap is acceptable
- [err-catch-unwind-boundary](./err-catch-unwind-boundary.md) - catch_unwind only at an isolation edge
- [err-panic-message](./err-panic-message.md) - every intentional panic explains the violated contract
