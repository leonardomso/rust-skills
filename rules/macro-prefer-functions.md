# macro-prefer-functions

> Reach for a macro only when a function or generic cannot express it

## Why It Matters

Macros expand before type checking; the expanded Rust is still inferred and
type checked. The indirection can make navigation, diagnostics, compile time,
and edition-sensitive syntax harder to reason about, and a macro cannot be
passed around as a function value. A function or trait usually gives callers a
smaller, typed contract without promising any universal optimization benefit.

Reach for a macro only when you genuinely need one of: variadic argument counts, a DSL with non-Rust syntax, blanket trait impls across an open-ended set of types, compile-time format/string checks, or eliminating mechanically repetitive boilerplate that a function truly cannot handle. Expansion complexity is a warning sign: users should be able to predict the generated shape from the invocation. If they cannot, use an explicit API or code generation at build time.

## Bad

```rust
// Nothing here requires a macro — no variadic args, no DSL, no trait impl.
macro_rules! double {
    ($x:expr) => {
        $x * 2
    };
}

fn main() {
    let n = double!(21);
    println!("{n}");
}
```

## Good

```rust
// A generic function is clearer, debuggable, and just as efficient.
#[inline]
fn double<T>(x: T) -> T
where
    T: std::ops::Add<Output = T> + Copy,
{
    x + x
}

fn main() {
    let n = double(21_i32);
    println!("{n}");
}
```

## When to Reach for a Macro

| Situation | Use a macro? |
|-----------|-------------|
| Fixed argument count, any types | No — use generics |
| Truly variadic argument list (`vec![]`, `println!`) | Yes |
| Implementing a trait for many unrelated types | Yes — `macro_rules!` impl block |
| DSL / embedded syntax (SQL, HTML, regex literals) | Maybe — use the least powerful macro form that can express it |
| Compile-time format string validation | Yes — `format_args!` style |
| Boilerplate a derive could generate | Yes — `#[derive(...)]` proc-macro |
| Simple computation or type conversion | No — use a function or trait |

## See Also

- [anti-over-abstraction](anti-over-abstraction.md) - avoid unnecessary abstraction layers
- [type-generic-bounds](type-generic-bounds.md) - add trait bounds only where needed
- [macro-rules-hygiene](macro-rules-hygiene.md) - hygiene and `$crate` for declarative macros
- [macro-declarative-before-proc](macro-declarative-before-proc.md) - prefer inspectable `macro_rules!` expansion before procedural machinery
- [macro-no-rewrite-item](macro-no-rewrite-item.md) - do not let a macro lie about the written signature
