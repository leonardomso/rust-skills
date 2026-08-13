# name-short-items

> Keep item names to about two short words; drop crate prefixes and lean on familiar abbreviations

## Why It Matters

Rust APIs are used with the module path in scope. `billing::DistributedInvoiceIdentifier` repeats what the path already said and hides the noun. Prefer `RuntimeConfig`, `billing::Id`, and `HookFn`. Callers who hold two `Id` types qualify them at the use site instead of baking the module into every identifier.

## Bad

```rust
pub struct DistributedRuntimeConfiguration {
    pub request_timeout_ms: u64,
}

pub mod billing {
    pub struct BillingInvoiceId(pub u64);
}

pub mod shipping {
    pub struct ShippingParcelId(pub u64);
}

pub type CompletionCallbackFunction = fn(u32);

fn dispatch(id: billing::BillingInvoiceId) -> shipping::ShippingParcelId {
    shipping::ShippingParcelId(id.0)
}
```

## Good

```rust
pub struct RuntimeConfig {
    pub timeout_ms: u64,
}

pub mod billing {
    pub struct Id(pub u64);
}

pub mod shipping {
    pub struct Id(pub u64);
}

pub type HookFn = fn(u32);

fn dispatch(id: billing::Id) -> shipping::Id {
    shipping::Id(id.0)
}

fn main() {
    let _cfg = RuntimeConfig { timeout_ms: 10 };
    let _ = dispatch(billing::Id(1));
    let _hook: HookFn = |_| {};
}
```

## Key Points

- Compound **at most two short words** (`RuntimeConfig`, not `DistributedRuntimeConfiguration`).
- Do not prefix the item with its module or crate when the parent path already names the domain (`billing::Id`, not `billing::BillingInvoiceId`).
- When two short names collide, **qualify at the use site** (`fn dispatch(billing::Id) -> shipping::Id`) rather than lengthening both types.
- Prefer a **familiar abbreviation** over the long expansion (`Fn`, `Id`, `Config`, `Http`, `Tx`).
- A longer name is allowed when the extra words carry meaning the path cannot (`AtomicUsize`, a protocol-specific `HttpsConnectorBuilder`). Those exceptions must be rare in a given crate and you should be able to say why.
- Do **not** abbreviate into opacity (`CfgMgr`, `CbFnHdlr`, `GAppCfg`). If a reader has to expand the name to understand it, keep the ordinary word (`name-no-weasel`).

## See Also

- [name-no-weasel](name-no-weasel.md) - drop empty `Service` / `Manager` / `Factory` padding first
- [name-types-camel](name-types-camel.md) - short names still use `UpperCamelCase`
- [name-acronym-word](name-acronym-word.md) - `Http`, not `HTTP`, inside the short name
- [name-crate-no-rs](name-crate-no-rs.md) - the crate name does not need a `-rs` suffix either
- [name-funcs-snake](name-funcs-snake.md) - functions stay `snake_case` even when abbreviated
