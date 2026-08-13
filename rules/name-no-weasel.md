# name-no-weasel

> Drop empty role words like `Service`, `Manager`, and `Factory` from type names

## Why It Matters

Every type manages something; putting `Manager` in the name does not tell a reader what the type *does*. Drop empty role words like `Service`, `Manager`, and `Factory`: replace them with the noun for the work (`Invoices`, `InvoiceDispatcher`) and use `Builder` when the type exists to construct another value. Shorter, specific names also survive grepping and rustdoc search.

## Bad

```rust
// Role word says nothing about invoices.
pub struct InvoiceService {
    pub count: usize,
}

// Every type "manages" something; the noun is missing.
pub struct LedgerManager {
    pub live: usize,
}

pub struct ReceiptFactory;

impl ReceiptFactory {
    pub fn create(&self) -> u64 {
        1
    }
}
```

## Good

```rust
pub struct Invoices {
    pub count: usize,
}

pub struct InvoiceDispatcher {
    pub live: usize,
}

pub struct ReceiptBuilder {
    seed: u64,
}

impl ReceiptBuilder {
    pub fn new() -> Self {
        Self { seed: 1 }
    }

    pub fn build(self) -> u64 {
        self.seed
    }
}

fn main() {
    let _ = ReceiptBuilder::new().build();
}
```

## Factories and Lifecycle

Do not pass a `FooFactory` merely to create values later. Accept the capability
you need:

```rust
fn populate(make_receipt: impl Fn() -> u64) -> Vec<u64> {
    (0..3).map(|_| make_receipt()).collect()
}

fn main() {
    assert_eq!(populate(|| 7), vec![7, 7, 7]);
}
```

Likewise, do not invent a `ResourceManager` whose job is disposal. Put cleanup
in the resource's `Drop` implementation so every ownership path follows the
same lifecycle. Keep `Builder` only for a genuine staged constructor with
optional or permutation-heavy configuration.

## See Also

- [name-types-camel](name-types-camel.md) - casing still follows UpperCamelCase after the extra words come out
- [name-crate-no-rs](name-crate-no-rs.md) - the same rule at crate scope: do not pad a name with a redundant suffix
- [api-builder-pattern](api-builder-pattern.md) - the idiomatic name for a repeated constructor is `FooBuilder`
