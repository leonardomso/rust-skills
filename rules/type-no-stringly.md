# type-no-stringly

> Model fixed value sets as enums and semantic values as validated newtypes, and parse strings once at the boundary

## Why It Matters

Strings accept any value—typos, wrong formats, invalid data all compile fine. Enums, newtypes, and validated types catch errors at compile time or construction time, not runtime. They also provide better IDE support, documentation, and make invalid states unrepresentable.

## Bad

```rust
// Status as string - easy to get wrong
fn set_status(status: &str) {
    match status {
        "pending" => { ... }
        "active" => { ... }
        "completed" => { ... }
        _ => panic!("Unknown status"),  // Runtime error
    }
}

// Easy to misuse
set_status("pending");   // OK
set_status("Pending");   // Runtime error - wrong case
set_status("aktive");    // Runtime error - typo
set_status("done");      // Runtime error - wrong word

// Configuration as strings
fn configure(key: &str, value: &str) {
    // No type safety, no validation
}

// Easy to swap arguments - compiles!
fn process_order(status: &str, priority: &str) {}
fn demo() {
    process_order("high", "pending");
}

// Any string is accepted, and IDs can be confused with each other
struct User { email: String, user_id: String }
```

## Good

```rust
// Status as enum - compile-time safety
enum Status {
    Pending,
    Active,
    Completed,
}

fn set_status(status: Status) {
    match status {
        Status::Pending => {}
        Status::Active => {}
        Status::Completed => {}
    }  // Exhaustive - compiler checks all cases
}

fn main() {
    // Can only pass valid values
    set_status(Status::Pending);  // OK
    // set_status(Status::Aktivev);  // would not compile: no such variant, typo caught
}

// Configuration with typed fields
struct Config {
    timeout: std::time::Duration,
    retries: u32,
    mode: Mode,
}

enum Mode { Fast, Safe, Balanced }

// Distinct types make swapped arguments a compile error
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
enum Priority { Low, Medium, High }

fn process_order(status: Status, priority: Priority) {}

fn demo() {
    process_order(Status::Completed, Priority::High);
    // process_order(Priority::High, Status::Pending); // compile error: swapped
}
```

## Parsing at Boundaries

```rust
use std::str::FromStr;

#[derive(Debug, Clone, Copy)]
enum Priority {
    Low,
    Medium,
    High,
}

impl FromStr for Priority {
    type Err = ParseError;
    
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "low" => Ok(Priority::Low),
            "medium" | "med" => Ok(Priority::Medium),
            "high" => Ok(Priority::High),
            _ => Err(ParseError::UnknownPriority(s.to_string())),
        }
    }
}

// Parse once at boundary
fn handle_request(priority_str: &str) -> Result<(), Error> {
    let priority: Priority = priority_str.parse()?;
    // From here, priority is type-safe
    process(priority);
    Ok(())
}
```

## Validated Newtypes

```rust
// Instead of string for email
struct Email(String);

impl Email {
    fn new(s: &str) -> Result<Self, ValidationError> {
        if is_valid_email(s) {
            Ok(Email(s.to_string()))
        } else {
            Err(ValidationError::InvalidEmail)
        }
    }
}

// Instead of string for IDs, so they can't be mixed up
struct UserId(u64);
struct PhoneNumber(String);

// Instead of string for paths
struct ConfigPath(PathBuf);

struct User {
    email: Email,       // must be valid
    phone: PhoneNumber,
    user_id: UserId,    // can't be confused with other IDs
}
```

## With Serde

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
enum EventType {
    UserCreated,
    UserDeleted,
    UserUpdated,
}

// JSON: {"type": "user_created", ...}
// Automatically validated during deserialization
```

## See Also

- [type-newtype-validated](./type-newtype-validated.md) - Validated newtypes
- [type-enum-states](./type-enum-states.md) - Enums for states
- [api-newtype-safety](./api-newtype-safety.md) - Newtype pattern
- [api-parse-dont-validate](./api-parse-dont-validate.md) - Parse at boundaries
- [type-newtype-ids](./type-newtype-ids.md) - Type-safe IDs
