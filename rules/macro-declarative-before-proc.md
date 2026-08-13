# macro-declarative-before-proc

> Prefer `macro_rules!` over a procedural macro whenever the transform can be written by example

## Why It Matters

A `macro_rules!` expansion is still tokens you can `cargo expand`, jump to, and review. A procedural macro is a compiler plugin: rust-analyzer often cannot show what it emitted, and every dependent crate pays to compile that plugin plus its `syn` graph. Prefer inspectability and low compile cost: start with a macro-by-example and introduce a proc-macro crate only when the job genuinely needs the AST.

## Bad

```rust
// Imagined `#[invoice_id]` attribute from a `proc-macro = true` crate.
// The expansion is not in this tree. Reviewers cannot read it without
// expanding a plugin, and every consumer now compiles that plugin.
pub struct InvoiceId(u64);

impl InvoiceId {
    pub const fn from_raw(raw: u64) -> Self {
        Self(raw)
    }
}

fn main() {
    let _ = InvoiceId::from_raw(7);
}
```

## Good

```rust
macro_rules! invoice_id {
    ($name:ident) => {
        #[derive(Clone, Copy, Debug, Eq, PartialEq)]
        pub struct $name(u64);

        impl $name {
            pub const fn from_raw(raw: u64) -> Self {
                Self(raw)
            }

            pub const fn as_raw(self) -> u64 {
                self.0
            }
        }
    };
}

invoice_id!(InvoiceId);
invoice_id!(OrderId);

fn main() {
    let id = InvoiceId::from_raw(7);
    assert_eq!(id.as_raw(), 7);
    let _ = OrderId::from_raw(1);
}
```

## When a Proc Macro Is Required

| Need | `macro_rules!` enough? |
|------|------------------------|
| Repeat a newtype, inherent impl, or simple `impl Trait` | Yes |
| Inspect named fields, attributes, or generics on a user type | No — custom derive |
| Parse non-Rust input (SQL, HTML, a config DSL) | No — function-like proc macro |
| Attach an attribute that must walk the item's AST | No — attribute proc macro |
| Variadic Rust tokens with no parsing beyond fragments | Yes (`vec!`, `matches!`) |

If a function or generic already expresses the idea, write that instead (`macro-prefer-functions`). When a proc macro is the right tool, keep it in its own crate (`macro-proc-two-crate`) and leave the written item's kind and signature alone (`macro-no-rewrite-item`).

## See Also

- [macro-prefer-functions](macro-prefer-functions.md) - try a function before any macro
- [macro-proc-two-crate](macro-proc-two-crate.md) - isolate the plugin when a proc macro is justified
- [macro-proc-syn-quote](macro-proc-syn-quote.md) - parse and emit with syn and quote
- [macro-no-rewrite-item](macro-no-rewrite-item.md) - generated tokens must not lie about the written signature
- [macro-no-implied-items](macro-no-implied-items.md) - do not smuggle extra types out of the expansion
