# lint-deny-correctness

> Keep `clippy::correctness` at deny: its lints flag code that is outright wrong

## Why It Matters

Clippy's correctness lints catch code that is outright wrong - logic errors, undefined behavior, or code that doesn't do what you think. These should always be errors, not warnings.

## Setup

```rust
// At the top of lib.rs or main.rs
#![deny(clippy::correctness)]
```

Or in `Cargo.toml`:

```toml
[lints.clippy]
correctness = { level = "deny", priority = -1 }
```

`clippy::correctness` is already deny-by-default. Setting it explicitly documents the intent and keeps it denied if someone adds a blanket `allow`.

## What It Catches

```rust
// infinite_iter: consuming an infinite iterator never returns
let n = std::iter::repeat(1).count();  // ERROR: infinite iteration

// impossible_comparisons
if x > 5 && x < 3 {  // ERROR: can never be true
}

// self_assignment
x = x;  // ERROR: no effect
```

## Important Correctness Lints

```rust
// approx_constant - using imprecise PI, E values
let pi = 3.14;  // Use std::f64::consts::PI

// invalid_regex - regex that won't compile
let re = Regex::new("[");  // Invalid regex

// iter_next_loop - using .next() in for loop incorrectly
for x in iter.next() {  // Should be: for x in iter
}

// never_loop - loop that never actually loops
loop {
    break;  // Always breaks immediately
}

// nonsensical_open_options - impossible file options
File::options().read(false).write(false).open("f");

// unit_cmp - comparing unit type ()
if foo() == bar() { }  // Both return (), always true
```

## Full Recommended Lints

```rust
#![deny(clippy::correctness)]
#![warn(clippy::suspicious)]
#![warn(clippy::style)]
#![warn(clippy::complexity)]
#![warn(clippy::perf)]

// For published crates
#![warn(missing_docs)]
#![warn(clippy::cargo)]
```

## Running Clippy

```bash
# Basic check
cargo clippy

# With all warnings as errors
cargo clippy -- -D warnings

# Check specific lint category
cargo clippy -- -W clippy::correctness

# In CI (fail on warnings), see lint-build-warnings
CARGO_BUILD_WARNINGS=deny cargo clippy --all-targets
```

## See Also

- [lint-warn-suspicious](lint-warn-suspicious.md) - Warn on suspicious code
- [lint-warn-perf](lint-warn-perf.md) - Warn on performance issues
- [lint-build-warnings](lint-build-warnings.md) - Deny warnings in CI with `build.warnings`
