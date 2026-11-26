# doc-first-sentence

> Make the first sentence of a doc comment a short, one-line summary of about 15 words or fewer

## Why It Matters

Rustdoc takes the first sentence of a doc comment as the summary shown in module and search listings. A long first sentence wraps across several lines and makes the listing hard to scan. Put the one-line summary first, then a blank line, then the details. The standard library follows this pattern throughout.

## Bad

```rust
/// Parses a configuration file from the given path, merging values from the environment and applying defaults for anything that is missing, and returns the result.
pub fn load(path: &str) -> String {
    path.to_owned()
}
```

## Good

```rust
/// Loads the configuration at `path`.
///
/// Values from the environment override the file, and missing keys fall back
/// to their defaults. The merged result is returned as text.
pub fn load(path: &str) -> String {
    path.to_owned()
}
```

## See Also

- [doc-all-public](doc-all-public.md) - Document every public item
- [doc-module-inner](doc-module-inner.md) - Module-level documentation
- [doc-examples-section](doc-examples-section.md) - Add runnable examples after the summary
- Source: Microsoft Pragmatic Rust Guidelines, M-FIRST-DOC-SENTENCE
