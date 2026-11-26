# macro-export-crate-path

> Export declarative macros with `#[macro_export]` and a clean import path

## Why It Matters

`#[macro_export]` lifts a macro to the crate root, making it importable like any other item. Combined with `$crate::` paths (see `macro-rules-hygiene`), the macro works regardless of how callers import it. Since Rust 2018, callers can use ordinary path imports (`use mycrate::my_macro;`) rather than the legacy `#[macro_use] extern crate mycrate;`, which polluted the global namespace and depended on item ordering.

## Bad

```rust
// lib.rs — legacy style
// Requires callers to write `#[macro_use] extern crate mylib;`
// and dumps all macros into the caller's global scope.
macro_rules! greet {
    ($name:expr) => {
        println!("hello, {}", $name);
    };
}
```

```rust
// consumer/src/main.rs — legacy
#[macro_use]
extern crate mylib; // order-sensitive; pollutes namespace

fn main() {
    greet!("world");
}
```

## Good

```rust
// lib.rs — modern style
#[macro_export]
macro_rules! greet {
    ($name:expr) => {
        // No trailing `;`: the macro stays usable in expression position.
        $crate::__private::print_greeting($name)
    };
}

// `#[macro_export]` already makes `use mylib::greet;` work.
// Do not add `pub use greet;` at the crate root: that is error E0255.
```

```rust
// consumer/src/main.rs — modern
use mylib::greet;

fn main() {
    greet!("world");
}
```

## Placing Macros in Modules

`#[macro_export]` always places the macro at the crate root regardless of where the `macro_rules!` definition appears. To expose it under a module path, use a `pub use` re-export:

```rust
// lib.rs
pub mod macros {
    // The macro is defined at crate root by #[macro_export], but we
    // also re-export it here so `use mycrate::macros::greet;` works.
    pub use crate::greet;
}

#[macro_export]
macro_rules! greet {
    ($name:expr) => { println!("hello, {}", $name); };
}
```

## Key Points

- Prefer `use mycrate::my_macro;` — it is explicit and plays well with `rustfmt` and IDEs.
- Avoid `#[macro_use]` in new code; it is required only when supporting pre-2018 edition consumers.
- If the macro calls internal helpers, pair `#[macro_export]` with `$crate::__private::...` paths.
- Do not end a macro expansion with a stray `;` when the macro can be used as an expression. Since Rust 1.99 the `semicolon_in_expressions_from_non_local_macros` lint warns about this for macros from other crates too, and it is a future-incompatibility warning.
- Document macros with `///` just like any other public item.

## See Also

- [macro-rules-hygiene](macro-rules-hygiene.md) - using `$crate` for correct item resolution
- [macro-private-helpers](macro-private-helpers.md) - hiding helpers used by exported macros
- [proj-workspace-deps](proj-workspace-deps.md) - workspace dependency inheritance
