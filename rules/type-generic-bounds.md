# type-generic-bounds

> Add trait bounds only where needed, prefer where clauses for readability

## Why It Matters

Trait bounds constrain what types can be used with generic code. Adding unnecessary bounds limits flexibility. Adding bounds in the right place (impl vs function vs where clause) affects usability and readability. Well-placed bounds keep APIs flexible while ensuring type safety.

## Bad

```rust
// Bounds on struct definition - limits all uses
struct Container<T: Clone + Debug> {  // Even storage requires Clone?
    items: Vec<T>,
}

// Inline bounds make signature hard to read
fn process<T: Clone + Debug + Send + Sync + 'static, E: Error + Send + Clone>(
    value: T
) -> Result<T, E> { ... }

// Redundant bounds
fn print_twice<T: Clone + Debug>(value: T)
where
    T: Clone,  // Already specified above
{ ... }
```

## Good

```rust
use std::error::Error;
use std::fmt::Debug;

// No bounds on struct - store anything
struct Container<T> {
    items: Vec<T>,
}

// Bounds only on impls that need them
impl<T: Clone> Container<T> {
    fn duplicate(&self) -> Self {
        Container { items: self.items.clone() }
    }
}

impl<T: Debug> Container<T> {
    fn debug_print(&self) {
        println!("{:?}", self.items);
    }
}

// Where clause for readability
fn process<T, E>(value: T) -> Result<T, E>
where
    T: Clone + Debug + Send + Sync + 'static,
    E: Error + Send + Clone,
{
    Ok(value)
}
```

## Bound Placement

```rust
// On struct: affects all uses of the type
struct MustBeClone<T: Clone> { data: T }  // Rarely needed

struct Container<T> { items: Vec<T> }

// On impl: affects specific functionality
impl<T: Clone> Container<T> {
    fn duplicate(&self) -> Self {
        Container { items: self.items.clone() }
    }
}  // Common pattern

// On function: affects that function only
fn requires_send<T: Send>(value: T) {
    let _ = value;
}

// Recommendation: start with no bounds, add as needed
```

## Where Clause Benefits

```rust
use std::fmt::Debug;

// Inline: hard to read
fn complex_inline<T: Clone + Debug + Send, U: AsRef<str> + Into<String>>(t: T, u: U) {
    let _ = (t, u);
}

// Where clause: clear and scannable
fn complex_where<T, U>(t: T, u: U)
where
    T: Clone + Debug + Send,
    U: AsRef<str> + Into<String>,
{
    let _ = (t, u);
}

// Essential for complex bounds
fn foo<T, U>(t: T, u: U)
where
    T: Iterator<Item = U>,
    U: Clone + Into<String>,
    Vec<U>: Debug,  // Bounds on expressions
{
    let _ = (t, u);
}
```

## Implied Bounds

```rust
use std::fmt::Debug;

// Supertrait bounds are implied
trait Foo: Clone + Debug {}

fn process_foo<T: Foo>(value: T) {
    // T: Clone and T: Debug are implied by T: Foo
    let cloned = value.clone();
    println!("{:?}", cloned);
}

// Associated type bounds
fn process_iter<I>(iter: I)
where
    I: Iterator,
    I::Item: Clone,  // Bound on associated type
{
    let _ = iter;
}
```

## Conditional Trait Implementation

```rust
use std::fmt::{self, Debug, Formatter};

struct Wrapper<T>(T);

// Implement Clone only when T: Clone
impl<T: Clone> Clone for Wrapper<T> {
    fn clone(&self) -> Self {
        Wrapper(self.0.clone())
    }
}

// Implement Debug only when T: Debug  
impl<T: Debug> Debug for Wrapper<T> {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        f.debug_tuple("Wrapper").field(&self.0).finish()
    }
}

// Wrapper<i32> is Clone + Debug
// Wrapper<NonCloneable> is neither
```

## See Also

- [api-impl-into](./api-impl-into.md) - Using Into bounds
- [api-impl-asref](./api-impl-asref.md) - Using AsRef bounds
- [name-type-param-single](./name-type-param-single.md) - Type parameter naming
- [trait-dyn-vs-generic](./trait-dyn-vs-generic.md) - Static vs dynamic dispatch
- [trait-associated-type-vs-generic](./trait-associated-type-vs-generic.md) - Associated types vs generics
