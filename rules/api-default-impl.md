# api-default-impl

> Implement `Default` for types with sensible default values

## Why It Matters

`Default` is a standard trait that provides a canonical way to create a default instance. It integrates with many ecosystem patterns: `Option::unwrap_or_default()`, `#[derive(Default)]`, struct update syntax `..Default::default()`, and generic code that requires `T: Default`. Implementing it makes your types more ergonomic.

## Bad

```rust
struct Config {
    timeout: Duration,
    retries: u32,
    verbose: bool,
}

impl Config {
    // Custom constructor - works but non-standard
    fn new() -> Self {
        Config {
            timeout: Duration::from_secs(30),
            retries: 3,
            verbose: false,
        }
    }
}

// Can't use with standard patterns
let config: Config = Default::default();  // Error: Default not implemented
let timeout = settings.get("timeout").unwrap_or_default();  // Won't work
```

## Good

Derive when every field's own default is right (`Duration::ZERO`, `0`, `false`, `""`, `[]`):

```rust
use std::time::Duration;

#[derive(Default)]
struct Simple {
    timeout: Duration,
    retries: u32,
    name: String,
    items: Vec<i32>,
}
```

For non-zero defaults, implement `Default` by hand. (Per-field defaults like `timeout: Duration = Duration::from_secs(30)` need the nightly `default_field_values` feature.)

```rust
use std::collections::HashMap;
use std::time::Duration;

struct Config {
    timeout: Duration,
    retries: u32,
    verbose: bool,
}

impl Default for Config {
    fn default() -> Self {
        Config {
            timeout: Duration::from_secs(30),
            retries: 3,
            verbose: false,
        }
    }
}

fn main() {
    let config = Config::default();
    let config = Config { retries: 5, ..Default::default() };
    let map: HashMap<&str, String> = HashMap::new();
    let value = map.get("key").cloned().unwrap_or_default();
    let _ = (config, value);
}
```

## Builder with Default

`Default` gives a builder its starting state.

```rust
#[derive(Default)]
struct ServerBuilder {
    host: String,
    port: u16,
}

impl ServerBuilder {
    fn host(mut self, host: impl Into<String>) -> Self {
        self.host = host.into();
        self
    }

    fn port(mut self, port: u16) -> Self {
        self.port = port;
        self
    }
}

fn main() {
    let _server = ServerBuilder::default().host("0.0.0.0").port(3000);
}
```

## When Not to Implement Default

If a field has no sensible default, don't implement `Default`. A `Default` that produces an invalid value is worse than none. Provide a constructor (or a builder with required fields) instead.

```rust
struct UserId(u64);

struct User {
    id: UserId, // no sensible default
    name: String,
}

impl User {
    fn new(id: UserId, name: impl Into<String>) -> Self {
        User { id, name: name.into() }
    }
}
```

## Generic Code

`#[derive(Default)]` on a generic type adds a `T: Default` bound. Implement `Default` by hand when the type doesn't need `T` to be `Default`:

```rust
use std::marker::PhantomData;

struct Wrapper<T> {
    _marker: PhantomData<T>,
}

impl<T> Default for Wrapper<T> {
    fn default() -> Self {
        Wrapper { _marker: PhantomData }
    }
}

fn create_or_default<T: Default>(opt: Option<T>) -> T {
    opt.unwrap_or_default()
}
```

## See Also

- [api-builder-pattern](./api-builder-pattern.md) - Building complex types
- [api-common-traits](./api-common-traits.md) - Other common traits to implement
- [api-from-not-into](./api-from-not-into.md) - Conversion traits
