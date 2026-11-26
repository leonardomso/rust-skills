# own-copy-small

> Implement `Copy` for small, simple types

## Why It Matters

Types that implement `Copy` are implicitly duplicated on assignment instead of moved. This eliminates the need for explicit `.clone()` calls and makes the code more ergonomic. For small types (roughly ≤16 bytes), copying is as fast or faster than passing a pointer. Rust itself puts no size limit on `Copy` (a `[u8; 1024]` is `Copy`); the size bands below are performance heuristics, and value semantics matter as much as size.

## Bad

```rust
// Small type without Copy - requires explicit clone
#[derive(Clone, Debug)]
struct Point {
    x: f64,
    y: f64,
}

fn distance(p1: Point, p2: Point) -> f64 {
    ((p2.x - p1.x).powi(2) + (p2.y - p1.y).powi(2)).sqrt()
}

let origin = Point { x: 0.0, y: 0.0 };
let target = Point { x: 3.0, y: 4.0 };

let d1 = distance(origin.clone(), target.clone()); // Tedious
let d2 = distance(origin.clone(), target.clone()); // Every use needs clone
// origin and target still usable but verbose
```

## Good

```rust
// Small type with Copy - implicit duplication
#[derive(Clone, Copy, Debug)]
struct Point {
    x: f64,
    y: f64,
}

fn distance(p1: Point, p2: Point) -> f64 {
    ((p2.x - p1.x).powi(2) + (p2.y - p1.y).powi(2)).sqrt()
}

let origin = Point { x: 0.0, y: 0.0 };
let target = Point { x: 3.0, y: 4.0 };

let d1 = distance(origin, target); // Implicitly copied
let d2 = distance(origin, target); // Still works!
// origin and target remain valid
```

## Copy Requirements

A type can implement `Copy` only if:
1. All fields implement `Copy`
2. No custom `Drop` implementation
3. No heap-allocated data (`String`, `Vec`, `Box`, etc.)

```rust
// ✅ Can be Copy
#[derive(Clone, Copy)]
struct Color {
    r: u8,
    g: u8,
    b: u8,
    a: u8,
}

// ❌ Cannot be Copy - contains String
#[derive(Clone)]
struct Person {
    name: String,  // String is not Copy
    age: u32,
}

// ❌ Cannot be Copy - has Drop
struct FileHandle {
    fd: i32,
}
impl Drop for FileHandle {
    fn drop(&mut self) { /* close file */ }
}
```

## Size Guidelines

Heuristics, not language rules — measure if it matters:

| Size | Recommendation |
|------|----------------|
| ≤ 16 bytes | Implement `Copy` |
| 17-64 bytes | Consider `Copy`, benchmark if critical |
| > 64 bytes | Probably don't, prefer references |

```rust
use std::mem::size_of;

#[derive(Clone, Copy)]
struct SmallId(u64); // 8 bytes ✅

#[derive(Clone, Copy)]
struct Rect { x: f32, y: f32, w: f32, h: f32 } // 16 bytes ✅

#[derive(Clone)] // No Copy - 72 bytes
struct Transform {
    matrix: [[f64; 3]; 3], // 72 bytes, too large
}
```

## Common Copy Types

Standard library types that are `Copy`:
- All primitives: `i32`, `f64`, `bool`, `char`, etc.
- Shared references: `&T` (note: `&mut T` is NOT `Copy` — copying a mutable reference would alias it, so it is reborrowed instead)
- Raw pointers: `*const T`, `*mut T`
- Function pointers: `fn(T) -> U`
- Tuples of `Copy` types: `(i32, f64)`
- Arrays of `Copy` types: `[u8; 32]`
- `Option<T>` where `T: Copy`
- `PhantomData<T>`

## See Also

- [own-clone-explicit](./own-clone-explicit.md) - When Clone without Copy is appropriate
- [type-newtype-ids](./type-newtype-ids.md) - Newtype pattern often uses Copy
