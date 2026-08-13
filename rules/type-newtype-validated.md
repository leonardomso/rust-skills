# type-newtype-validated

> Use newtypes to enforce validation at construction time

## Why It Matters

A private newtype plus invariant-preserving constructors can guarantee stable,
context-free properties of its inner value. It cannot permanently prove
authorization, reachability, uniqueness, revocation, or any fact that depends
on external state. Name the exact invariant and re-check contextual facts at
the effect boundary.

## Bad

```rust
// Validation scattered throughout code
fn send_email(to: &str, body: &str) -> Result<(), Error> {
    if !is_valid_email(to) {  // Must check every time
        return Err(Error::InvalidEmail);
    }
    // ...
}

fn add_recipient(list: &mut Vec<String>, email: &str) -> Result<(), Error> {
    if !is_valid_email(email) {  // Check again
        return Err(Error::InvalidEmail);
    }
    list.push(email.to_string());
    Ok(())
}
```

## Good

```rust
#[derive(Clone, PartialEq, Eq, Hash)]
pub struct BoundedLabel(String);

impl BoundedLabel {
    pub const MAX_BYTES: usize = 64;

    pub fn new(value: String) -> Result<Self, LabelError> {
        if value.is_empty() {
            return Err(LabelError::Empty);
        }
        if value.len() > Self::MAX_BYTES {
            return Err(LabelError::TooLong);
        }
        if !value.chars().all(|c| c.is_alphanumeric() || matches!(c, '-' | '_')) {
            return Err(LabelError::InvalidCharacter);
        }
        Ok(Self(value))
    }
    
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

fn create_resource(label: BoundedLabel) -> Resource {
    Resource { label }
}
```

## Common Validated Types

```rust
// URLs
pub struct Url(url::Url);

impl Url {
    pub fn parse(s: &str) -> Result<Self, UrlError> {
        url::Url::parse(s)
            .map(Url)
            .map_err(UrlError::from)
    }
}

// Non-empty strings
pub struct NonEmptyString(String);

impl NonEmptyString {
    pub fn new(s: String) -> Option<Self> {
        if s.is_empty() {
            None
        } else {
            Some(NonEmptyString(s))
        }
    }
}

// Positive numbers
pub struct PositiveI32(i32);

impl PositiveI32 {
    pub fn new(n: i32) -> Option<Self> {
        if n > 0 {
            Some(PositiveI32(n))
        } else {
            None
        }
    }
    
    pub fn get(&self) -> i32 {
        self.0
    }
}

// Bounded ranges
pub struct Percentage(f64);

impl Percentage {
    pub fn new(value: f64) -> Result<Self, RangeError> {
        if (0.0..=100.0).contains(&value) {
            Ok(Percentage(value))
        } else {
            Err(RangeError::OutOfBounds)
        }
    }
}
```

## With Serde

```rust
use serde::{Deserialize, Serialize};

#[derive(Clone, Serialize)]
pub struct Email(String);

impl<'de> Deserialize<'de> for Email {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        Email::new(&s).map_err(serde::de::Error::custom)
    }
}

// JSON deserialization routes through the same constructor. Ensure Email's
// Debug and errors redact PII instead of embedding the rejected input.
let email: Email = serde_json::from_str(r#""user@example.com""#)?;
```

## Compile-Time Validation

```rust
pub struct Month(u8);

impl Month {
    pub const fn new(value: u8) -> Option<Self> {
        if value >= 1 && value <= 12 {
            Some(Self(value))
        } else {
            None
        }
    }
}

const JANUARY: Month = match Month::new(1) {
    Some(month) => month,
    None => panic!("BUG: January literal is in 1..=12"),
};
```

Every conversion from a weaker representation is fallible. Do not implement
`From<String>` or `From<u8>` when some inputs violate the invariant; use
`TryFrom`, `FromStr`, or a constructor returning a proper error. An additional
constant can unwrap the checked result so an invalid literal fails at compile
time without making ordinary runtime construction panic.

## See Also

- [api-parse-dont-validate](./api-parse-dont-validate.md) - Parse at boundaries
- [api-newtype-safety](./api-newtype-safety.md) - Type-safe distinctions
- [type-newtype-ids](./type-newtype-ids.md) - ID newtypes
- [conv-fromstr-parsing](./conv-fromstr-parsing.md) - FromStr for validated parsing
- [serde-try-from-validate](./serde-try-from-validate.md) - Validate during deserialization
