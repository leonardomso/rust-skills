# pat-if-let-guards

> Use `if let` match guards to bind data needed only by one arm

## Why It Matters

A boolean match guard can test a condition, but it cannot bind the successful value of a fallible operation for the arm body. That often leads to duplicated parsing, a nested `match`, or an `unwrap()` after an `is_ok()` check. Rust 1.95 stabilized `if let` guards: the guard can destructure a value and keep its bindings in scope for the selected arm. Use them when a pattern identifies the candidate and one additional fallible match decides whether the arm applies.

## Bad

```rust
enum Command {
    SetPort(String),
    Stop,
}

fn apply(command: Command) -> Option<u16> {
    match command {
        Command::SetPort(raw) if raw.parse::<u16>().is_ok() => {
            // Parses twice and relies on the guard staying in sync.
            Some(raw.parse::<u16>().unwrap())
        }
        Command::SetPort(_) | Command::Stop => None,
    }
}
```

## Good

```rust
enum Command {
    SetPort(String),
    Stop,
}

fn apply(command: Command) -> Option<u16> {
    match command {
        Command::SetPort(raw)
            if let Ok(port) = raw.parse::<u16>()
                && port != 0 =>
        {
            Some(port)
        }
        Command::SetPort(_) | Command::Stop => None,
    }
}
```

The `port` binding exists only in the guarded arm. If parsing fails or the following condition is false, matching continues with the next arm.

## Key Points

- Use an `if let` guard when the extra binding belongs to one match arm; use an if-let chain when the whole operation is naturally an `if` expression.
- Guard expressions may run while the matched value is only conditionally selected. Keep them free of externally visible side effects.
- Preserve a fallback arm: a guarded pattern does not make the unguarded cases exhaustive.
- Prefer a nested `match` when different failure variants need different behavior rather than collapsing them into a guard miss.

## See Also

- [pat-if-let-chains](pat-if-let-chains.md) - combine bindings and boolean conditions in an `if` header
- [pat-exhaustive-enum](pat-exhaustive-enum.md) - handle every enum variant explicitly
- [pat-let-else](pat-let-else.md) - extract a pattern and return early on failure
