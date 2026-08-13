# anti-transliterated-port

> Port domain behavior into Rust; do not copy the source language's types, errors, or runtime architecture

## Why It Matters

A mechanical C#, Java, C++, or Python translation keeps the business rules and also keeps the other language's answers to *its* problems. Split those layers: an invoice total or a customer lookup can follow the same steps, but errors, ownership, threads, traits, lifetimes, process-wide cells, and "inspect the type at runtime" dispatch are Rust problems. Constructs that have no Rust counterpart (managed reflection) and constructs that only *look* familiar (process statics) both fail — the second often months later. Matching method names and inputs for the domain is fine. Matching the foreign architecture is a warning sign.

## Bad

```rust
use std::sync::OnceLock;

/// Source-language null guard. Rust arguments are already present.
pub fn require_name(name: Option<&str>) -> &str {
    name.expect("customer name required")
}

/// Interface soup plus a process-wide service slot.
pub trait ICustomerStore {
    fn get_by_id(&self, id: i64) -> Option<String>;
}

static STORE: OnceLock<String> = OnceLock::new();

/// Stringly method dispatch standing in for reflection.
pub fn invoke(op: &str, id: i64) -> Option<String> {
    match op {
        "GetById" => STORE.get().filter(|_| id >= 0).cloned(),
        _ => None,
    }
}

```

## Good

```rust
pub struct CustomerId(pub u64);

pub struct Customer {
    pub id: CustomerId,
    pub name: String,
}

#[derive(Debug, PartialEq)]
pub enum LookupError {
    Missing,
}

/// Domain steps stay the same as any other language: walk the rows, add cents.
pub fn invoice_total(cents: &[u32]) -> u32 {
    cents.iter().copied().sum()
}

/// Ownership and errors are Rust-shaped: borrow the table, return `Result`.
pub fn customer_name<'a>(
    rows: &'a [Customer],
    id: CustomerId,
) -> Result<&'a str, LookupError> {
    rows.iter()
        .find(|row| row.id.0 == id.0)
        .map(|row| row.name.as_str())
        .ok_or(LookupError::Missing)
}

/// A trait here is a Rust behavior bound, not an `IFoo` header.
pub trait Store {
    fn name(&self, id: CustomerId) -> Result<String, LookupError>;
}

/// Rust concurrency makes ownership and joining explicit.
pub fn total_in_parallel(left: &[u32], right: &[u32]) -> u32 {
    std::thread::scope(|scope| {
        let a = scope.spawn(|| invoice_total(left));
        let b = scope.spawn(|| invoice_total(right));
        a.join().unwrap() + b.join().unwrap()
    })
}

fn main() {
    let rows = [Customer {
        id: CustomerId(7),
        name: "ada".into(),
    }];
    assert_eq!(invoice_total(&[100, 40]), 140);
    assert_eq!(total_in_parallel(&[100], &[40]), 140);
    assert_eq!(customer_name(&rows, CustomerId(7)).unwrap(), "ada");
}
```

## Key Points

- Keep portable domain logic (formulas, table rules, state machines). Rewrite the language-specific architecture.
- **Errors:** `Result` and typed error values, not exceptions, `null` checks, or `expect` as control flow.
- **Ownership:** decide who owns each parameter. Do not clone every argument because the source language passed references or `IDisposable` wrappers.
- **Concurrency:** use Rust tasks, threads, and channels. Do not recreate a foreign thread-pool or `Task.Run` singleton.
- **Traits:** a trait is not a C#/Java interface and not a base class. No abstract service hierarchies "so we can mock."
- **Lifetimes:** component scope is a lifetime or an owned value, not a finalizer or a `using` block translated into `Drop` theater.
- **Statics:** a `static` registry or service locator is the other ecosystem's default. It splits under duplicate crate versions and fights tests (`proj-avoid-statics`).
- **Reflection-like patterns:** Rust has no useful general reflection. Do not dispatch on type names, method-name strings, or runtime attribute bags.
- Type and method *names* may resemble the original product language. If the Rust side still has the same managers, locators, and null guards, the architecture did not move.

## See Also

- [err-result-over-panic](err-result-over-panic.md) - recoverable failures are `Result`, not a translated exception
- [own-borrow-over-clone](own-borrow-over-clone.md) - ownership of parameters is a Rust decision
- [api-service-clone](api-service-clone.md) - make component ownership and sharing explicit
- [conc-scoped-threads](conc-scoped-threads.md) - borrow local work across threads instead of a static pool
- [trait-dyn-vs-generic](trait-dyn-vs-generic.md) - traits are not ported interfaces
- [proj-avoid-statics](proj-avoid-statics.md) - statics look familiar and fail later
- [anti-over-abstraction](anti-over-abstraction.md) - class-hierarchy ports are over-abstraction
