# name-weasel-words

> Avoid names built on `Service`, `Manager`, `Factory`, and similar words that say nothing about what the type does

## Why It Matters

Almost all code manages, serves, or produces something, so these words add no information. `BookingManager` does not tell a reader whether it stores, validates, schedules, or sends bookings. A name that states the actual job is easier to find and review, and it keeps types from growing into catch-all objects. Object lifetimes in Rust are handled by ownership and `Drop`, not by a manager.

## Bad

```rust
pub struct Booking;

pub struct BookingManager {
    pending: Vec<Booking>,
}

pub struct ConnectionFactory;

// Asking for a factory object imports an OO pattern
pub fn run_all(factory: &ConnectionFactory) {
    let _ = factory;
}
```

## Good

```rust
pub struct Booking;

// Says what it does with bookings
pub struct BookingDispatcher {
    pending: Vec<Booking>,
}

pub struct Connection;

// A closure expresses "make me one of these" without a factory type
pub fn run_all(connect: impl Fn() -> Connection) {
    let _conn = connect();
}
```

## Notes

- Name the specific behavior: `Scheduler`, `Dispatcher`, `Validator`, `Registry`, or just the plural noun, such as `Bookings`.
- A type whose job is to assemble another type step by step is a `Builder`. See [api-builder-pattern](api-builder-pattern.md).
- A variable named `booking_service` is fine; the weasel word is the problem in type and trait names.

## See Also

- [api-builder-pattern](api-builder-pattern.md) - `Builder` is the Rust name for a factory
- [name-types-camel](name-types-camel.md) - Type naming conventions
- [closure-fn-trait-bounds](closure-fn-trait-bounds.md) - Accept closures instead of factory objects
- Source: Microsoft Pragmatic Rust Guidelines, M-WEASEL-WORDS
