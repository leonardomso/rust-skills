# type-never-diverge

> Use `!` (never type) for functions that never return

## Why It Matters

The never type `!` indicates a function will never return normally—it either loops forever, panics, or exits the process. This helps the compiler understand control flow and enables `!` to coerce to any type, making it useful in match arms and expressions.

## Bad

```rust
// Return type doesn't indicate non-returning
fn infinite_loop() {
    loop {
        process_events();
    }
    // Implicit () return type, but never returns
}

// Using Option when it always panics
fn unreachable_code() -> Option<()> {
    panic!("This should never be called");
}
```

## Good

```rust
// ! indicates function never returns
fn infinite_loop() -> ! {
    loop {
        process_events();
    }
}

fn abort_with_error(msg: &str) -> ! {
    eprintln!("Fatal error: {}", msg);
    std::process::exit(1);
}

fn panic_handler() -> ! {
    panic!("Unexpected state");
}
```

## Coercion to Any Type

```rust
// ! coerces to any type
fn get_value(opt: Option<i32>) -> i32 {
    match opt {
        Some(v) => v,
        None => panic!("No value"),  // panic! returns !, coerces to i32
    }
}

// Useful in Result handling
fn must_get_config() -> Config {
    match load_config() {
        Ok(c) => c,
        Err(e) => {
            log_error(&e);
            std::process::exit(1)  // Returns !, coerces to Config
        }
    }
}
```

## Standard Library Examples

```rust
// std::process::exit has the signature: fn exit(code: i32) -> !
// std::hint::unreachable_unchecked is: unsafe fn unreachable_unchecked() -> !
// The panic! macro expands to an expression of type !

// loop {} with no break
fn forever() -> ! {
    loop {}
}
```

## In Match Expressions

```rust
enum State {
    Running,
    Stopped,
    Error,
}

fn get_status(state: &State) -> &str {
    match state {
        State::Running => "running",
        State::Stopped => "stopped",
        State::Error => unreachable!(),  // ! coerces to &str
    }
}

// With Result
fn process(r: Result<Data, Error>) -> Data {
    match r {
        Ok(d) => d,
        Err(e) => panic!("Unexpected error: {}", e),  // ! coerces to Data
    }
}
```

## Diverging Closures

```rust
// Closures that never return
let handler: fn() -> ! = || {
    panic!("Handler called");
};

// In thread spawn
std::thread::spawn(|| -> ! {
    loop {
        process_work();
    }
});
```

## Never Type as a Type Argument

`fn f() -> !` has been stable since Rust 1.41. Since Rust 1.100 `!` is stable everywhere, so it can be a type argument. Use it for an error type that cannot occur, and the compiler lets you skip the impossible `Err` arm.

```rust
fn always_ok() -> Result<u32, !> {
    Ok(7)
}

fn main() {
    // Irrefutable: an `Err(!)` arm cannot exist
    let Ok(n) = always_ok();
    assert_eq!(n, 7);
}
```

`std::convert::Infallible` is now a type alias for `!` (Rust 1.100), so the two are the same type and interchangeable. Existing code that names `Infallible`, such as `FromStr::Err` or `TryFrom::Error`, keeps compiling.

```rust
use std::convert::Infallible;

fn same_type(x: Infallible) -> ! {
    x // Infallible and ! are the same type
}
```

Also stable in 1.100: never-type fallback is `!` on every edition (it was `()` before 2024), and `!` implements `AsRef<T>` and `AsMut<T>`. If an old closure or generic call relied on the `()` fallback, add an explicit type annotation.

## See Also

- [err-result-over-panic](./err-result-over-panic.md) - When to panic vs return Result
- [type-result-fallible](./type-result-fallible.md) - Result for errors
- [opt-cold-unlikely](./opt-cold-unlikely.md) - Marking unlikely paths
- [conv-tryfrom-fallible](./conv-tryfrom-fallible.md) - `Infallible` as the error of a conversion that cannot fail
