# doc-alias-suggestions

> Add `#[doc(alias = "...")]` so users and rustc find an item under the name they expect

## Why It Matters

Users arrive with names from other languages and libraries: `erase`, `delete`, `pop_back`, `strlen`. `#[doc(alias)]` makes rustdoc search find your item under those names. Since Rust 1.99, rustc also uses doc aliases: when a method call fails with "no method named `x`", an exact doc-alias match is suggested before a similarity search over other method names. One attribute helps both docs readers and compiler errors.

## Bad

```rust
pub struct Registry {
    items: Vec<String>,
}

impl Registry {
    /// Removes every entry.
    pub fn clear(&mut self) {
        self.items.clear();
    }
}

// registry.erase()  -> error: no method named `erase`, no hint about `clear`
```

## Good

```rust
pub struct Registry {
    items: Vec<String>,
}

impl Registry {
    /// Removes every entry.
    #[doc(alias = "erase")]
    #[doc(alias = "delete_all")]
    pub fn clear(&mut self) {
        self.items.clear();
    }
}
```

Search for `erase` in rustdoc now finds `Registry::clear`, and calling `registry.erase()` gets a suggestion to use `clear`.

## Guidelines

- Add aliases for names that users of similar APIs really use, not for every synonym.
- Put the alias on the item the user should call. One item can have several `doc(alias)` attributes.
- Aliases do not create the name. The code still does not compile with the alias.
- An alias must not contain a quote character or start or end with a space.

## See Also

- [doc-all-public](doc-all-public.md) - document public items
- [doc-intra-links](doc-intra-links.md) - link related items
- [name-no-get-prefix](name-no-get-prefix.md) - consistent method names
