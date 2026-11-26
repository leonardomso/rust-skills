# trait-dyn-vs-generic

> Default to generics and `impl Trait`; use `dyn Trait` only for mixed types, runtime choice, or plug-ins

## Why It Matters

Generic bounds and `impl Trait` monomorphize at compile time: each concrete type gets its own specialised copy that the compiler can inline and optimise, but every distinct type adds to binary size. `dyn Trait` stores a fat pointer (data + vtable) and dispatches at runtime, producing a single code path — necessary when you must store heterogeneous values or return erased types, at the cost of one pointer indirection per call. Choosing the wrong option either leaves performance on the table or prevents heterogeneous collections entirely. Default to generics for hot, simple code; reach for `dyn` when you need flexibility, heap storage, or cross-crate plug-ins.

## Bad

```rust
// Using `dyn` everywhere "to be flexible" — blocks inlining and
// forces heap allocation even for single, known types.
trait Shape {
    fn area(&self) -> f64;
}

struct Circle { radius: f64 }
impl Shape for Circle {
    fn area(&self) -> f64 { std::f64::consts::PI * self.radius * self.radius }
}

// Unnecessary boxing when only one concrete type is used.
fn total_area(shapes: &[Box<dyn Shape>]) -> f64 {
    shapes.iter().map(|s| s.area()).sum()
}

// Boxing returns that have one concrete type
fn get_iterator() -> Box<dyn Iterator<Item = i32>> {
    Box::new((0..10).map(|x| x * 2))
}

```

## Good

```rust
use std::fmt;

trait Shape {
    fn area(&self) -> f64;
    fn name(&self) -> &str;
}

#[derive(Clone)]
struct Circle { radius: f64 }
#[derive(Clone)]
struct Rect { w: f64, h: f64 }

impl Shape for Circle {
    fn area(&self) -> f64 { std::f64::consts::PI * self.radius * self.radius }
    fn name(&self) -> &str { "circle" }
}
impl Shape for Rect {
    fn area(&self) -> f64 { self.w * self.h }
    fn name(&self) -> &str { "rect" }
}

// --- Static dispatch: use when the type is known and performance matters ---
// Monomorphized; the compiler can inline `area()`.
fn total_area_generic<S: Shape>(shapes: &[S]) -> f64 {
    shapes.iter().map(|s| s.area()).sum()
}

// Also fine with `impl Trait` in argument position (same monomorphization).
fn print_area(shape: &impl Shape) {
    println!("{}: {:.2}", shape.name(), shape.area());
}

// --- Dynamic dispatch: use for heterogeneous collections or plugin-like APIs ---
fn total_area_dyn(shapes: &[Box<dyn Shape>]) -> f64 {
    shapes.iter().map(|s| s.area()).sum()
}

// Return `impl Trait` when the type is known: no heap, inlined
fn get_iterator() -> impl Iterator<Item = i32> {
    (0..10).map(|x| x * 2)
}

fn demo() {
    // Homogeneous slice — zero boxing, static dispatch.
    let circles = [Circle { radius: 1.0 }, Circle { radius: 2.0 }];
    println!("{:.2}", total_area_generic(&circles));

    // Heterogeneous collection — `dyn` is the right tool.
    let shapes: Vec<Box<dyn Shape>> = vec![
        Box::new(Circle { radius: 1.0 }),
        Box::new(Rect { w: 3.0, h: 4.0 }),
    ];
    println!("{:.2}", total_area_dyn(&shapes));
}
```

## Decision Table

| Situation | Prefer |
|---|---|
| Single known concrete type | `impl Trait` / generic |
| Hot path, inlining critical | Generic bound |
| Heterogeneous collection (`Vec<Box<dyn …>>`) | `dyn Trait` |
| Storing trait objects across calls | `dyn Trait` |
| Returning erased type from `fn` | `Box<dyn Trait>` or `impl Trait` (static) |
| Binary size matters, many monomorphisations | `dyn Trait` |
| Closed, known set of types | `enum` |
| Plug-in / callback registered at runtime | `dyn Trait` |

## When `dyn` Is Right

- A heterogeneous collection: `Vec<Box<dyn Handler>>` holding different handler types.
- A type chosen at runtime, such as a database backend picked from config (`fn create(cfg) -> Box<dyn Database>`).
- A plug-in or callback registered at runtime.
- Recursive structures whose child types are open-ended.

## Pattern: Enum Instead of `dyn`

When the set of types is closed and known, an enum gives static dispatch with no heap allocation.

```rust
use std::f64::consts::PI;

enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

impl Shape {
    fn area(&self) -> f64 {
        match self {
            Shape::Circle { radius } => PI * radius * radius,
            Shape::Rectangle { width, height } => width * height,
        }
    }
}
```

## `impl Trait` in Traits

Return-position `impl Trait` in traits is stable since Rust 1.75. Use it when callers need not name the type, and an associated type when they do.

## See Also

- [type-generic-bounds](type-generic-bounds.md) - add trait bounds only where needed
- [anti-over-abstraction](anti-over-abstraction.md) - excessive generics
- [mem-box-large-variant](mem-box-large-variant.md) - boxing enum variants
- [closure-static-vs-dyn](closure-static-vs-dyn.md) - same tradeoff for closures
- [trait-object-safety](trait-object-safety.md) - keep traits dyn-compatible when you need `dyn Trait`
