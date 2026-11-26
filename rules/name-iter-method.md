# name-iter-method

> Name iterator methods `iter()`, `iter_mut()`, and `into_iter()`, and implement `IntoIterator` for owned, `&`, and `&mut`

## Why It Matters

Rust has a strong convention for iterator method names. Following these conventions makes your types work predictably with `for` loops and iterator adapters. Users expect `iter()` for shared references, `iter_mut()` for mutable references, and `into_iter()` for owned iteration.

## Bad

```rust
struct Collection<T> {
    items: Vec<T>,
}

impl<T> Collection<T> {
    // Non-standard names - confusing (also `iterate`, `get_items`, `as_iter`)
    fn elements(&self) -> impl Iterator<Item = &T> {
        self.items.iter()
    }
    
    fn get_iterator(&self) -> impl Iterator<Item = &T> {
        self.items.iter()
    }
    
    fn to_iter(self) -> impl Iterator<Item = T> {
        self.items.into_iter()
    }
}
```

## Good

```rust
struct Collection<T> {
    items: Vec<T>,
}

impl<T> Collection<T> {
    /// Returns an iterator over references.
    fn iter(&self) -> impl Iterator<Item = &T> {
        self.items.iter()
    }
    
    /// Returns an iterator over mutable references.
    fn iter_mut(&mut self) -> impl Iterator<Item = &mut T> {
        self.items.iter_mut()
    }
}

// Implement IntoIterator for for-loop support
impl<T> IntoIterator for Collection<T> {
    type Item = T;
    type IntoIter = std::vec::IntoIter<T>;
    
    fn into_iter(self) -> Self::IntoIter {
        self.items.into_iter()
    }
}

impl<'a, T> IntoIterator for &'a Collection<T> {
    type Item = &'a T;
    type IntoIter = std::slice::Iter<'a, T>;
    
    fn into_iter(self) -> Self::IntoIter {
        self.items.iter()
    }
}

impl<'a, T> IntoIterator for &'a mut Collection<T> {
    type Item = &'a mut T;
    type IntoIter = std::slice::IterMut<'a, T>;
    
    fn into_iter(self) -> Self::IntoIter {
        self.items.iter_mut()
    }
}
```

## Iterator Convention Summary

| Method | Receiver | Yields | Use Case |
|--------|----------|--------|----------|
| `iter()` | `&self` | `&T` | Read-only iteration |
| `iter_mut()` | `&mut self` | `&mut T` | In-place modification |
| `into_iter()` | `self` | `T` | Consuming iteration |

## For Loop Integration

```rust
let col = Collection { items: vec![1, 2, 3] };

// These all work with proper IntoIterator impls
for item in &col {           // Calls (&col).into_iter() -> iter()
    println!("{}", item);    // &i32
}

for item in &mut col {       // Calls (&mut col).into_iter() -> iter_mut()
    *item += 1;              // &mut i32
}

for item in col {            // Calls col.into_iter()
    process(item);           // i32, consumes col
}
```

## Additional Iterator Methods

Domain-specific iterators use descriptive names and follow the same ownership pattern.

```rust
impl<T> Collection<T> {
    /// Iterates over the items that pass a check.
    fn iter_valid(&self) -> impl Iterator<Item = &T> {
        self.items.iter().filter(|_| true)
    }

    /// Iterates over a sub-range.
    fn iter_range(&self, start: usize, end: usize) -> impl Iterator<Item = &T> {
        self.items[start..end].iter()
    }
}
```

The standard library follows the same pattern for maps:

```rust
use std::collections::HashMap;

fn demo(mut map: HashMap<String, i32>) {
    for (_k, _v) in map.iter() {}      // (&K, &V)
    for (_k, _v) in map.iter_mut() {}  // (&K, &mut V)
    for _k in map.keys() {}            // &K
    for _v in map.values() {}          // &V
    for (_k, _v) in map.drain() {}     // (K, V), leaves the map empty
}
```

## See Also

- [name-as-free](./name-as-free.md) - Conversion naming conventions
- [api-extension-trait](./api-extension-trait.md) - Iterator extensions
- [name-iter-type-match](./name-iter-type-match.md) - Iterator type naming
- [perf-iter-over-index](./perf-iter-over-index.md) - Prefer iterators
- [api-common-traits](./api-common-traits.md) - Standard trait implementations
