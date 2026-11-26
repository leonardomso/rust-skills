# api-newtype-safety

> Use newtypes to prevent mixing semantically different values

## Why It Matters

Raw primitives like `u64` or `String` carry no semantic meaning. A function taking `(u64, u64)` can easily be called with arguments swapped. Newtypes wrap primitives in distinct types, making the compiler catch mistakes at compile time rather than runtime.

## Bad

```rust
struct User {
    id: u64,
    group_id: u64,
    created_at: u64,  // Unix timestamp
}

fn add_user_to_group(user_id: u64, group_id: u64) { ... }

// Bug: arguments swapped - compiles fine, fails at runtime
let user = User { id: 100, group_id: 5, created_at: 1234567890 };
add_user_to_group(user.group_id, user.id);  // Silent bug!

// Bug: wrong field used - timestamp passed as ID
add_user_to_group(user.created_at, user.group_id);  // Compiles fine!
```

## Good

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
struct UserId(u64);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
struct GroupId(u64);

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
struct Timestamp(u64);

struct User {
    id: UserId,
    group_id: GroupId,
    created_at: Timestamp,
}

fn add_user_to_group(user_id: UserId, group_id: GroupId) { }

fn main() {
    let user = User { id: UserId(1), group_id: GroupId(7), created_at: Timestamp(0) };
    add_user_to_group(user.id, user.group_id);  // Fine
}
```

The mix-ups no longer compile:

```rust,compile_fail
struct UserId(u64);
struct GroupId(u64);
struct Timestamp(u64);
struct User { id: UserId, group_id: GroupId, created_at: Timestamp }

fn add_user_to_group(user_id: UserId, group_id: GroupId) { }

fn main() {
    let user = User { id: UserId(1), group_id: GroupId(7), created_at: Timestamp(0) };

    // Error E0308: expected UserId, found GroupId
    add_user_to_group(user.group_id, user.id);

    // Error E0308: expected UserId, found Timestamp
    add_user_to_group(user.created_at, user.group_id);
}
```

## Derive Common Traits

```rust
use serde::{Deserialize, Serialize};

// Minimal: just enough for your use case
#[derive(Debug, Clone, Copy)]
struct MeterId(u32);

// Full ID type: hashable, comparable, displayable
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
struct OrderId(u64);

impl std::fmt::Display for OrderId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "ORD-{:08}", self.0)
    }
}

// With serde for serialization
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(transparent)]  // Serializes as raw u64
struct ProductId(u64);
```

## Constructor Patterns

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct Email(String);

#[derive(Debug)]
enum EmailError { InvalidFormat }

fn is_valid_email(s: &str) -> bool { s.contains('@') }

impl Email {
    /// Creates a new Email, validating the format.
    pub fn new(s: &str) -> Result<Self, EmailError> {
        if is_valid_email(s) {
            Ok(Email(s.to_string()))
        } else {
            Err(EmailError::InvalidFormat)
        }
    }
    
    /// Returns the email as a string slice.
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

// Usage enforces validation
fn signup() -> Result<(), EmailError> {
    let email = Email::new("user@example.com")?;  // Must go through validation
    Ok(())
}
```

## Zero-Cost Abstraction

```rust
use std::mem::size_of;

#[derive(Clone, Copy)]
struct Miles(f64);

#[derive(Clone, Copy)]
struct Kilometers(f64);

// Same size as raw f64
assert_eq!(size_of::<Miles>(), size_of::<f64>());
assert_eq!(size_of::<Kilometers>(), size_of::<f64>());

fn drive(distance: Miles) { }

// Explicit conversion
impl From<Kilometers> for Miles {
    fn from(km: Kilometers) -> Self {
        Miles(km.0 * 0.621371)
    }
}

let km = Kilometers(100.0);
drive(km.into());  // Explicit, visible conversion
```

Passing the wrong unit does not compile:

```rust,compile_fail
struct Miles(f64);
struct Kilometers(f64);

fn drive(distance: Miles) { }

fn main() {
    let km = Kilometers(100.0);
    drive(km);  // Error E0308: expected Miles, found Kilometers
}
```

## When Newtypes Help Most

```rust
// ✅ IDs that could be confused
struct AccountId(u64);
struct Money(u64);
fn transfer(from: AccountId, to: AccountId, amount: Money) { }

// ✅ Units that shouldn't mix
struct Celsius(f64);
struct Fahrenheit(f64);

// ✅ Validated strings
struct Username(String);  // Validated alphanumeric
struct Password(String);  // Never logged

// ✅ Different meanings of same type
struct Milliseconds(u64);
struct Seconds(u64);

// ❌ Overkill: single use, no confusion possible
struct X(i32);  // Just use i32
```

## See Also

- [type-newtype-ids](./type-newtype-ids.md) - Newtype pattern for IDs
- [api-parse-dont-validate](./api-parse-dont-validate.md) - Type-driven validation
- [own-copy-small](./own-copy-small.md) - Making newtypes Copy
- [api-dont-leak-types](api-dont-leak-types.md) - Keep third-party types out of public APIs
