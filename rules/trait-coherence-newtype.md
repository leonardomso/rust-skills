# trait-coherence-newtype

> Respect the orphan rule; wrap a foreign type in a newtype to implement a foreign trait on it

## Why It Matters

Rust's coherence rules ensure that compatible crates cannot introduce
overlapping implementations. For the common `impl Trait for Type` form, a
foreign trait can be implemented when the self type is local. The complete
orphan rule also considers trait input types, fundamental wrappers, and the
position of uncovered type parameters, so “trait or self type is local” is a
useful common case rather than the full algorithm. When both `Display` and
`Vec<i32>` are foreign, wrap the vector in a local newtype and implement the
trait on that local type.

## Bad

```rust
use std::fmt;

// error[E0117]: only traits defined in the current crate can be implemented for
// types defined outside of the crate
// impl fmt::Display for Vec<i32> { ... }  // both `Display` and `Vec` are foreign
```

## Good

```rust
use std::fmt;

// A local newtype wrapping the foreign type. This formatting abstraction does
// not promise an ABI, so it does not need a repr attribute.
struct CommaSeparated(Vec<i32>);

impl CommaSeparated {
    pub fn new(v: Vec<i32>) -> Self { Self(v) }

    // Provide access to the inner value.
    pub fn into_inner(self) -> Vec<i32> { self.0 }
    pub fn inner(&self) -> &[i32] { &self.0 }
}

// Now both the trait (Display) is foreign and the type (CommaSeparated) is local —
// the orphan rule is satisfied because CommaSeparated is defined here.
impl fmt::Display for CommaSeparated {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let mut iter = self.0.iter().peekable();
        while let Some(n) = iter.next() {
            write!(f, "{n}")?;
            if iter.peek().is_some() {
                write!(f, ", ")?;
            }
        }
        Ok(())
    }
}

// Implement From/Into so conversion is ergonomic.
impl From<Vec<i32>> for CommaSeparated {
    fn from(v: Vec<i32>) -> Self { Self(v) }
}

impl From<CommaSeparated> for Vec<i32> {
    fn from(w: CommaSeparated) -> Self { w.0 }
}

fn demo() {
    let nums = CommaSeparated::new(vec![1, 2, 3, 4, 5]);
    println!("{nums}");   // "1, 2, 3, 4, 5"

    // Round-trip through the inner type.
    let v: Vec<i32> = nums.into();
    let again = CommaSeparated::from(v);
    println!("{again}");
}
```

## Key Points

- A blanket `impl<T> ForeignTrait for ForeignType<T>` has no local type and is
  rejected. A local type in a trait argument can affect the full orphan check;
  rely on the compiler and the Reference for less common generic forms.
- Use `#[repr(transparent)]` only when same-ABI layout is an intentional FFI
  contract. It does not make arbitrary `transmute` or pointer casts safe;
  validity, provenance, aliasing, and ownership still apply.
- Provide `From`/`Into` conversions and an `inner()` / `into_inner()` accessor so callers can move in and out of the wrapper easily.
- The newtype pattern is described in the Rust API Guidelines under "Newtypes provide static distinctions" (rust-lang.github.io/api-guidelines/).
- Newtype wrappers are also the correct way to add trait impls to types from transitive dependencies that you do not control.

## See Also

- [api-newtype-safety](api-newtype-safety.md) - use newtypes for type-safe distinctions
- [type-repr-transparent](type-repr-transparent.md) - use `#[repr(transparent)]` for FFI newtypes
- [trait-blanket-impl](trait-blanket-impl.md) - give behaviour to every type meeting a bound
- [api-from-not-into](api-from-not-into.md) - implement `From`, not `Into` (auto-derived)
