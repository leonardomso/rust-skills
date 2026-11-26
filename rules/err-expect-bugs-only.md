# err-expect-bugs-only

> Reserve `expect()` for violated invariants that indicate bugs; return `Result` for user input, I/O, network, and database failures

## Why It Matters

`expect()` is better than `unwrap()` because it provides context, but it still panics. Reserve it for situations where failure indicates a bug in your code—a violated invariant, not a user error or external failure. The message should explain why the invariant should hold, helping future developers understand and fix the bug.

## Bad

```rust
// User input can legitimately fail - don't expect
fn parse_user_input(input: &str) -> Config {
    serde_json::from_str(input)
        .expect("Invalid JSON")  // User error, not a bug!
}

// Network can fail - don't expect
fn fetch_data(url: &str) -> Data {
    reqwest::get(url)
        .expect("Network request failed")  // External failure!
        .json()
        .expect("Invalid response")
}

// File might not exist - don't expect
fn load_config() -> Config {
    let content = fs::read_to_string("config.json")
        .expect("Config file missing");  // Environment issue!
}

// Database lookups can miss - don't expect
let user = db.find_user(id).await.expect("user not found");
```

## Good

```rust
use std::collections::HashMap;
use std::net::IpAddr;
use std::sync::Mutex;

type Value = u32;

#[derive(serde::Deserialize)]
struct Config {
    name: String,
}

const EMBEDDED_CONFIG: &str = r#"{ "name": "default" }"#;

struct Cache {
    cache: HashMap<String, Value>,
}

impl Cache {
    // Invariant: after insert, key exists
    fn cache_and_get(&mut self, key: String, value: Value) -> &Value {
        self.cache.insert(key.clone(), value);
        self.cache.get(&key)
            .expect("BUG: key must exist immediately after insert")
    }
}

// Invariant: the address is a compile-time constant
fn loopback() -> IpAddr {
    "127.0.0.1".parse()
        .expect("BUG: loopback address literal is invalid - this is a compile-time constant")
}

// Invariant: poisoning only happens after a panic elsewhere
fn lock_value(mutex: &Mutex<Value>) -> Value {
    let guard = mutex.lock().expect("BUG: mutex poisoned by an earlier panic");
    *guard
}

// Invariant: embedded data is checked in CI
fn embedded_config() -> Config {
    serde_json::from_str(EMBEDDED_CONFIG)
        .expect("BUG: embedded config is invalid")
}
```

## expect() Message Guidelines

Messages should:
1. Start with "BUG:" or similar to indicate it's an invariant
2. Explain WHY the invariant should hold
3. Help developers fix the issue

```rust
fn messages(map: &std::collections::HashMap<u8, u8>) {
    // ❌ Bad messages
    map.get(&1).expect("failed");                // No context
    map.get(&1).expect("should not be None");    // Doesn't explain why
    map.get(&1).expect("Invalid state");         // Vague

    // ✅ Good messages
    map.get(&1).expect("BUG: HashMap entry exists after insert");
    "42".parse::<u16>().expect("BUG: validated input must parse - validation is broken");
    "127.0.0.1".parse::<std::net::IpAddr>()
        .expect("BUG: static address literal is invalid - syntax error in source");
}
```

## Pattern: Validate Once, expect() After

```rust
struct ValidatedEmail(String);

impl ValidatedEmail {
    pub fn new(email: &str) -> Result<Self, EmailError> {
        // Validation happens here, returns Result
        if !is_valid_email(email) {
            return Err(EmailError::Invalid);
        }
        Ok(ValidatedEmail(email.to_string()))
    }
    
    pub fn domain(&self) -> &str {
        // After validation, expect() is fine
        self.0.split('@').nth(1)
            .expect("BUG: ValidatedEmail must contain @")
    }
}
```

## Alternatives When expect() Is Wrong

| Situation | Use |
|-----------|-----|
| User input, file/network I/O, database | `?` with error context |
| Sensible fallback exists | `unwrap_or` / `unwrap_or_default` |
| Needs logging or custom handling | `match` with a fallback |
| Value proven by validation or construction | `expect("BUG: ...")` |

```rust
use anyhow::Context;

#[derive(Debug)]
enum ConfigError { InvalidPort }

#[derive(Debug, thiserror::Error)]
enum Error {
    #[error("{0} not found")]
    NotFound(&'static str),
}

struct User;
async fn fetch(url: &str) -> Result<String, std::io::Error> { Ok(String::new()) }
async fn find_user(id: u64) -> Result<Option<User>, Error> { Ok(None) }

fn parse_port(input: &str) -> Result<u16, ConfigError> {
    // Don't: expect on user data
    // let port: u16 = input.parse().expect("Invalid port");

    // Do: Return Result
    let port: u16 = input.parse().map_err(|_| ConfigError::InvalidPort)?;
    Ok(port)
}

async fn load(url: &str, id: u64) -> anyhow::Result<User> {
    // Do: Add context to I/O and network errors
    let response = fetch(url).await.context("failed to fetch URL")?;
    let user = find_user(id).await?.ok_or(Error::NotFound("user"))?;
    Ok(user)
}

fn port_or_default(input: &str) -> u16 {
    // Do: Provide default
    input.parse().unwrap_or(8080)
}
```

## See Also

- [err-no-unwrap-prod](./err-no-unwrap-prod.md) - Avoiding unwrap in production
- [err-result-over-panic](./err-result-over-panic.md) - When to return Result
- [api-parse-dont-validate](./api-parse-dont-validate.md) - Type-driven validation
