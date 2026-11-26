# err-no-unwrap-prod

> Propagate errors with `?` or `expect` a documented invariant; keep `unwrap()` out of production paths

## Why It Matters

`unwrap()` panics on `None` or `Err` without any context about what went wrong. In production, this creates cryptic crash messages that are hard to debug. Either propagate errors with `?`, use `expect()` with a message explaining the invariant, or handle the error explicitly.

## Bad

```rust
fn process_request(req: Request) -> Response {
    let user_id = req.headers.get("X-User-Id").unwrap();  // Why did it fail?
    let user = database.find_user(user_id).unwrap();       // Which operation?
    let data = user.preferences.get("theme").unwrap();     // No context
    
    Response::new(data)
}

// Crash message: "called `Option::unwrap()` on a `None` value"
// Where? Why? No idea.

// Also crashes: missing file, bad input, closed channel
let content = std::fs::read_to_string("config.toml").unwrap();
let num: i32 = user_input.parse().unwrap();
let msg = receiver.recv().unwrap();
```

## Good

```rust
// Option 1: Propagate with ?
fn process_request(req: Request) -> Result<Response, AppError> {
    let user_id = req.headers
        .get("X-User-Id")
        .ok_or(AppError::MissingHeader("X-User-Id"))?;
    
    let user = database.find_user(user_id)?;
    
    let data = user.preferences
        .get("theme")
        .ok_or(AppError::MissingPreference("theme"))?;
    
    Ok(Response::new(data))
}

// Option 2: expect() for invariants (not user input)
fn get_config_value(&self, key: &str) -> &str {
    self.config
        .get(key)
        .expect("BUG: required config key missing after validation")
}

// Option 3: Provide defaults
fn get_theme(user: &User) -> &str {
    user.preferences
        .get("theme")
        .unwrap_or(&"default")
}

// Option 4: Match for complex handling
fn process_optional(value: Option<Data>) -> ProcessedData {
    match value {
        Some(data) => process(data),
        None => {
            log::warn!("No data provided, using fallback");
            ProcessedData::default()
        }
    }
}
```

## `expect()` vs `unwrap()`

`expect()` adds context to the panic message, so use it for invariants (see [err-expect-bugs-only](./err-expect-bugs-only.md)). If the failure can happen in normal operation, propagate instead.

```rust
// Bad: no context
let port = config.get("port").unwrap();

// Better: explains the invariant
let port = config.get("port")
    .expect("config must contain 'port' after validation");

// Best: propagate if it's not truly an invariant
let port = config.get("port")
    .ok_or_else(|| ConfigError::MissingKey("port"))?;
```

## Alternatives to unwrap()

| Situation | Use Instead |
|-----------|-------------|
| Can propagate error | `?` operator (`opt.ok_or(Error::Missing)?`) |
| Has sensible default | `unwrap_or()`, `unwrap_or_default()` |
| Default requires computation | `unwrap_or_else(\|\| ...)` |
| Internal invariant | `expect("explanation")` |
| Need to handle both cases | `match` or `if let` |
| Transform or chain | `map`, `and_then` |

## When unwrap() Is Acceptable

- Tests: a panic is the expected failure mode.
- Constant input known valid at compile time, such as a literal regex in a `LazyLock`.
- Right after a check that guarantees success; prefer `if let`, `last()`, or the entry API, which need no check at all.

```rust
use std::collections::HashMap;

fn first_or_default(map: &HashMap<String, i32>) -> i32 {
    // Preferred: no unwrap, no separate check
    map.get("key").copied().unwrap_or_default()
}

#[test]
fn parses_valid_input() {
    assert_eq!("42".parse::<i32>().unwrap(), 42);
}
```

## Clippy Lints

```toml
# Cargo.toml
[lints.clippy]
unwrap_used = "warn"      # Warn on unwrap()
expect_used = "warn"      # Also warn on expect() (stricter)
```

```rust
// Allow in specific places where it's justified
#[allow(clippy::unwrap_used)]
fn definitely_safe() {
    // Unwrap is safe here because...
    let x = Some(5).unwrap();
}
```

## See Also

- [err-result-over-panic](./err-result-over-panic.md) - Return Result instead of panicking
- [err-question-mark](./err-question-mark.md) - Use ? for propagation
- [err-expect-bugs-only](./err-expect-bugs-only.md) - When expect() is appropriate
