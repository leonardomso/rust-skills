# api-inherent-core

> Put a type's essential methods on the type itself; implement traits by forwarding to them

## Why It Matters

If the only way to call `extract_entry` is through a trait, every caller must discover and import that trait. Inherent methods show up on the type in rustdoc and in completion, so the common path needs no extra `use`. Keep traits as optional adapters: implement the work once on the type, then forward from the trait so generic code still compiles.

## Bad

```rust
pub trait Extract {
    fn extract_entry(&self, name: &str) -> String;
}

pub struct Archive;

impl Extract for Archive {
    fn extract_entry(&self, name: &str) -> String {
        format!("entry {name}")
    }
}

fn main() {
    let archive = Archive;
    // Does not compile until `Extract` is in scope.
    let _ = Extract::extract_entry(&archive, "readme.txt");
}
```

## Good

```rust
pub trait Extract {
    fn extract_entry(&self, name: &str) -> String;
}

pub struct Archive;

impl Archive {
    pub fn extract_entry(&self, name: &str) -> String {
        format!("entry {name}")
    }
}

impl Extract for Archive {
    fn extract_entry(&self, name: &str) -> String {
        Self::extract_entry(self, name)
    }
}

fn fetch_via_trait(archive: &impl Extract, name: &str) -> String {
    archive.extract_entry(name)
}

fn main() {
    let archive = Archive;
    let direct = archive.extract_entry("readme.txt");
    let via_trait = fetch_via_trait(&archive, "readme.txt");
    assert_eq!(direct, via_trait);
}
```

## See Also

- [api-extension-trait](api-extension-trait.md) - traits are for adding methods to foreign types, not hiding your own
- [api-sealed-trait](api-sealed-trait.md) - keep a trait implementable only by your crate when it is not a user hook
- [name-no-get-prefix](name-no-get-prefix.md) - name the inherent method the way callers already search for it
