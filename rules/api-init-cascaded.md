# api-init-cascaded

> Group four or more required constructor parameters into semantic helper types

## Why It Matters

A constructor with four or more required inputs is hard to scan and easy to
call incorrectly; repeated primitive types make the risk worse. Cascade that
initialization through helper types: group required parameters by meaning, then construct the outer
type from those groups. Check the Rust API Guidelines newtype pattern
(`C-NEWTYPE`) at the same time so `Origin` and `Destination` cannot be
transposed. This is not a builder. Builders exist for optional,
permutation-heavy configuration; cascading structures a long required
argument list.

## Bad

```rust
pub struct Shipment {
    origin: String,
    destination: String,
    unit: String,
    weight: u64,
}

impl Shipment {
    pub fn new(
        origin: &str,
        destination: &str,
        unit: &str,
        weight: u64,
    ) -> Self {
        Self {
            origin: origin.to_owned(),
            destination: destination.to_owned(),
            unit: unit.to_owned(),
            weight,
        }
    }
}

fn schedule() -> Shipment {
    Shipment::new("oslo", "helsinki", "kg", 500)
}
```

## Good

```rust
pub struct Origin(String);
pub struct Destination(String);

pub struct Route {
    origin: Origin,
    destination: Destination,
}

pub struct Load {
    unit: String,
    weight: u64,
}

pub struct Shipment {
    route: Route,
    load: Load,
}

impl Shipment {
    pub fn new(route: Route, load: Load) -> Self {
        Self { route, load }
    }
}

impl Route {
    pub fn new(origin: Origin, destination: Destination) -> Self {
        Self { origin, destination }
    }
}

impl Load {
    pub fn new(unit: impl Into<String>, weight: u64) -> Self {
        Self {
            unit: unit.into(),
            weight,
        }
    }
}

fn schedule() -> Shipment {
    let route = Route::new(Origin("oslo".into()), Destination("helsinki".into()));
    Shipment::new(route, Load::new("kg", 500))
}
```

Group only what is semantically one thing. `Route` owns two endpoints; `Load` owns a unit and weight. Do not invent a leftover bag type whose only job is to shorten the outer signature.

## Cascaded Init vs Builders

| Situation | Tool |
|---|---|
| Four or more required parameters | Cascade through semantic helper types; add newtypes where values can be confused |
| Up to two optional construction parameters | Inherent `new` / `with_*` methods |
| Four or more *permutations* of optional configuration | Builder (`api-builder-pattern`) |
| Required fields that still need a builder for the optionals | Group the required fields first, then hand that group to the builder |

A builder does not fix a four-string `new`. It only lets callers omit or reorder *optional* knobs. If the values are all required and same-shaped, group them. If they are optional and the call sites disagree about which subset is set, build. Use both when a type has a required semantic core *and* a large optional surface: cascade the core, then `Foo::builder(account)`.

Keep related parameters in one order across the helpers (`api-param-order`). The newtypes catch swaps that order alone cannot.

## See Also

- [api-builder-pattern](api-builder-pattern.md) - optional, permutation-heavy configuration; not a substitute for grouping required arguments
- [api-newtype-safety](api-newtype-safety.md) - `C-NEWTYPE`: distinct types so same-shaped values cannot be swapped
- [api-param-order](api-param-order.md) - keep the same conceptual parameters in the same order on every helper
- [type-newtype-ids](type-newtype-ids.md) - id newtypes are the usual first grouping
- [api-typestate](api-typestate.md) - when construction itself has ordered stages, encode the stages in the type
