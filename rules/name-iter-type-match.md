# name-iter-type-match

> Name iterator types after their source method

## Why It Matters

Iterator types should match the method that creates them. `iter()` returns `Iter`, `into_iter()` returns `IntoIter`, `keys()` returns `Keys`. This naming pattern is established by the standard library and makes types predictable.

## Standard Library Pattern

```rust
use std::collections::{hash_map, HashMap};
use std::{slice, vec};

// Vec (via slice)
let mut v = vec![1, 2, 3];
let _: slice::Iter<'_, i32> = v.iter();          // iter() -> Iter
let _: slice::IterMut<'_, i32> = v.iter_mut();   // iter_mut() -> IterMut
let _: vec::IntoIter<i32> = v.clone().into_iter(); // into_iter() -> IntoIter

// HashMap
let mut map: HashMap<String, i32> = HashMap::new();
let _: hash_map::Iter<'_, String, i32> = map.iter();
let _: hash_map::Keys<'_, String, i32> = map.keys();     // keys() -> Keys
let _: hash_map::Values<'_, String, i32> = map.values(); // values() -> Values
let _: hash_map::Drain<'_, String, i32> = map.drain();   // drain() -> Drain
```

## Implementation

```rust
mod my_collection {
    pub struct MyCollection<T> {
        items: Vec<T>,
    }
    
    // Iterator types in same module
    pub struct Iter<'a, T> {
        inner: std::slice::Iter<'a, T>,
    }
    
    pub struct IterMut<'a, T> {
        inner: std::slice::IterMut<'a, T>,
    }
    
    pub struct IntoIter<T> {
        inner: std::vec::IntoIter<T>,
    }
    
    impl<T> MyCollection<T> {
        pub fn iter(&self) -> Iter<'_, T> {
            Iter { inner: self.items.iter() }
        }
        
        pub fn iter_mut(&mut self) -> IterMut<'_, T> {
            IterMut { inner: self.items.iter_mut() }
        }
    }
    
    impl<T> IntoIterator for MyCollection<T> {
        type Item = T;
        type IntoIter = IntoIter<T>;
        
        fn into_iter(self) -> IntoIter<T> {
            IntoIter { inner: self.items.into_iter() }
        }
    }
    
    // Implement Iterator for each type
    impl<'a, T> Iterator for Iter<'a, T> {
        type Item = &'a T;
        fn next(&mut self) -> Option<Self::Item> {
            self.inner.next()
        }
    }
    
    impl<'a, T> Iterator for IterMut<'a, T> {
        type Item = &'a mut T;
        fn next(&mut self) -> Option<Self::Item> {
            self.inner.next()
        }
    }
    
    impl<T> Iterator for IntoIter<T> {
        type Item = T;
        fn next(&mut self) -> Option<Self::Item> {
            self.inner.next()
        }
    }
}
```

## Naming Convention

| Method | Iterator Type |
|--------|---------------|
| `iter()` | `Iter` |
| `iter_mut()` | `IterMut` |
| `into_iter()` | `IntoIter` |
| `keys()` | `Keys` |
| `values()` | `Values` |
| `values_mut()` | `ValuesMut` |
| `drain()` | `Drain` |
| `chunks()` | `Chunks` |
| `windows()` | `Windows` |

## Custom Iterator Methods

```rust
pub struct Graph {
    nodes: Vec<u32>,
    edges: Vec<(u32, u32)>,
}

// Method name -> Type name
pub struct Nodes<'a> {
    inner: std::slice::Iter<'a, u32>,
}

pub struct Edges<'a> {
    inner: std::slice::Iter<'a, (u32, u32)>,
}

impl Graph {
    pub fn nodes(&self) -> Nodes<'_> {
        Nodes { inner: self.nodes.iter() }
    }

    pub fn edges(&self) -> Edges<'_> {
        Edges { inner: self.edges.iter() }
    }
}

impl<'a> Iterator for Nodes<'a> {
    type Item = &'a u32;

    fn next(&mut self) -> Option<Self::Item> {
        self.inner.next()
    }
}

impl<'a> Iterator for Edges<'a> {
    type Item = &'a (u32, u32);

    fn next(&mut self) -> Option<Self::Item> {
        self.inner.next()
    }
}
```

## Bad

```rust
// Mismatched names
impl MyCollection<T> {
    fn iter(&self) -> MyCollectionIterator<'_, T> { }  // Should be Iter
    fn keys(&self) -> KeyIterator<'_, K> { }           // Should be Keys
}

// Generic names that don't match method
pub struct Iterator<T>;  // Conflicts with std::iter::Iterator
pub struct I<T>;         // Too cryptic
```

## See Also

- [name-iter-method](./name-iter-method.md) - iter/iter_mut/into_iter
- [api-common-traits](./api-common-traits.md) - Implementing common traits
