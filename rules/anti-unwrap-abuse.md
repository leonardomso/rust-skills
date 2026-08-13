# anti-unwrap-abuse

> Do not turn expected input, dependency, or lifecycle failures into panics

## Why It Matters

`unwrap()` panics on `None` or `Err`. In a service, a panic may abort one task, one request, or the whole process depending on runtime and panic policy; it can abandon work and trigger restart amplification. It also erases the boundary decision about retry, rejection, fallback, and observability. Return a typed error for failures that input, dependencies, configuration, shutdown, or races can cause.

## Bad

```rust
let content = std::fs::read_to_string("config.toml").unwrap();
let port: u16 = user_input.parse().unwrap();
let value = map.get("key").unwrap();
let message = receiver.recv().unwrap();
```

All four failures are possible without a Rust bug.

## Good

```rust
fn load_config(path: &std::path::Path) -> Result<Config, ConfigError> {
    let content = std::fs::read_to_string(path)
        .map_err(|source| ConfigError::Read { path: path.to_owned(), source })?;
    toml::from_str(&content)
        .map_err(|source| ConfigError::Parse { path: path.to_owned(), source })
}

fn parse_port(input: &str) -> Result<u16, ConfigError> {
    let port = input.parse::<u16>().map_err(ConfigError::Port)?;
    if port == 0 {
        return Err(ConfigError::ZeroPort);
    }
    Ok(port)
}

let value = map.get("key").ok_or(Error::MissingKey)?;

while let Ok(message) = receiver.recv() {
    handle(message)?;
}
```

A default is correct only when the product contract defines absence or invalidity as that value. Do not write `parse().unwrap_or(0)` when zero changes security, capacity, timeout, port, or retention behavior.

## Invariants

Use `expect` only when failure proves an internal invariant violation and the message states the invariant:

```rust
map.entry(key.clone()).or_insert(value);
let inserted = map
    .get(&key)
    .expect("BUG: entry API inserted or found this key");
use_value(inserted);
```

Prefer APIs such as `entry`, pattern matching, `NonZero*`, and validated newtypes that make the invariant direct. A prior check on mutable external state, the filesystem, network, clock, process environment, or another thread does not prove a later operation cannot fail.

## Tests

```rust
#[test]
fn parses_valid_port() {
    let parsed = parse_port("8080").expect("fixture is a valid non-zero port");
    assert_eq!(parsed, 8080);
}
```

A panic is an appropriate test failure, but `expect` preserves fixture intent. Add separate assertions for invalid inputs rather than unwrapping only the happy path.

## Static Initialization

A string literal can still become invalid when a dependency's parser changes. Preserve initialization failure when startup can report it:

```rust
use std::sync::OnceLock;

static PATTERN: OnceLock<regex::Regex> = OnceLock::new();

fn pattern() -> Result<&'static regex::Regex, regex::Error> {
    if let Some(value) = PATTERN.get() {
        return Ok(value);
    }
    let compiled = regex::Regex::new(r"^\d+$")?;
    Ok(PATTERN.get_or_init(|| compiled))
}
```

For a literal whose invalidity is treated as a build bug, a narrowly scoped `expect("BUG: ...")` at startup is defensible, but it is not compile-time validation unless a build-time/const mechanism actually checks it.

## Alternatives

- `?` propagates a typed failure while preserving its source chain.
- `ok_or`/`ok_or_else` turns absence into a domain error.
- `match` handles success, retry, closure, and shutdown distinctly.
- `unwrap_or_else` supplies a fallback only when the fallback is explicitly safe and observable.
- `checked_*` and `TryFrom` reject arithmetic/conversion failure.
- `let ... else` keeps an expected rejection path explicit.

## Enforcement

```toml
[lints.clippy]
unwrap_used = "deny"
expect_used = "warn"
```

Use narrow test-module or invariant-specific lint overrides with a reason. Do not globally allow unwraps in binaries, examples, benchmarks, or generated operational code.

## See Also

- [err-question-mark](err-question-mark.md) - propagate typed failures
- [err-expect-bugs-only](err-expect-bugs-only.md) - reserve `expect` for proved bugs
- [err-result-over-panic](err-result-over-panic.md) - define recoverable failure behavior
- [num-nonzero](num-nonzero.md) - encode invalid zero states out of the type
