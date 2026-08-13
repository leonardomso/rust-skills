# proj-cfg-select

> Use `cfg_select!` for one-of-many conditional items or expressions

## Why It Matters

Repeated `#[cfg(...)]` attributes make mutually exclusive platform branches hard to audit. Two predicates can overlap and define an item twice, or leave a supported target with no definition. Rust 1.95 stabilized `cfg_select!`, which evaluates branches in order and keeps only the first match. A visible `_` fallback makes the coverage decision explicit in one place.

## Bad

```rust
#[cfg(unix)]
fn path_separator() -> char {
    '/'
}

#[cfg(windows)]
fn path_separator() -> char {
    '\\'
}

// A new target needs another detached definition. Overlapping custom cfgs can
// also select two definitions and fail far from this code.
```

## Good

```rust
cfg_select! {
    unix => {
        fn path_separator() -> char {
            '/'
        }
    }
    windows => {
        fn path_separator() -> char {
            '\\'
        }
    }
    _ => {
        compile_error!("unsupported path platform");
    }
}

fn native_label() -> &'static str {
    cfg_select! {
        target_os = "linux" => "linux",
        target_os = "macos" => "macos",
        target_os = "windows" => "windows",
        _ => "other",
    }
}
```

## Key Points

- Branches are tested in source order; the first matching branch wins. Order overlapping predicates from most specific to least specific.
- Use `_` for an intentional fallback. Prefer `compile_error!` when an unsupported target must fail closed.
- `cfg_select!` works in item and expression position and is available from the prelude.
- Keep `check-cfg` declarations for custom cfg names. Selection does not validate spelling or allowed values.
- Use ordinary `#[cfg]` for one independent item; use `cfg_select!` when the branches represent one choice.

## See Also

- [lint-cfg-check](./lint-cfg-check.md) - declare custom cfg names and reject typos
- [proj-feature-additive](./proj-feature-additive.md) - keep Cargo features additive rather than mutually exclusive
- [proj-mod-by-feature](./proj-mod-by-feature.md) - organize feature-specific implementation code coherently
