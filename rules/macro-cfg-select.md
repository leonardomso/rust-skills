# macro-cfg-select

> Use `cfg_select!` (stable since Rust 1.95) to pick one compile-time branch instead of stacked `#[cfg]` or the `cfg-if` crate

## Why It Matters

`cfg_select!` evaluates a list of `cfg` predicates at compile time and emits only the code of the first one that is true. A `_ =>` arm is the fallback; with no match and no fallback, it is a compile error. It replaces the `cfg-if` crate with a std macro, works in item and expression position, and avoids the error-prone pattern of one `#[cfg(...)]` per item plus a hand-written negated `#[cfg(not(...))]` for the rest. Unselected arms are removed before type checking, which `if cfg!(...)` cannot do.

## Bad

```rust
// The negations must be kept in sync by hand, and a platform that matches
// none of them silently gets no function at all.
#[cfg(unix)]
fn path_separator() -> char {
    '/'
}

#[cfg(windows)]
fn path_separator() -> char {
    '\\'
}

// `cfg!` keeps both branches in the build, so each must compile everywhere.
fn config_dir() -> &'static str {
    if cfg!(windows) {
        windows_only::config_dir() // error on unix: module does not exist
    } else {
        "/etc/app"
    }
}
```

## Good

```rust
// Item position: exactly one `path_separator` is compiled.
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
        compile_error!("unsupported platform");
    }
}

fn main() {
    // Expression position: the arms need not all be valid on this target.
    let word_bits = cfg_select! {
        target_pointer_width = "64" => 64_u32,
        target_pointer_width = "32" => 32_u32,
        _ => 0_u32,
    };

    let kind = cfg_select! {
        all(unix, target_pointer_width = "64") => { "64-bit unix" }
        _ => { "other" }
    };

    println!("{} {} {}", path_separator(), word_bits, kind);
}
```

## Notes

- The first matching predicate wins, so put the most specific arm first. Since Rust 1.99 the `unreachable_cfg_select_predicates` lint (part of `unused`) warns about arms that can never be reached.
- Use `#[cfg(...)]` on a single item that is simply present or absent. Use `cfg_select!` when there are alternatives, or when you need an expression.
- Use `cfg!(...)` only when every branch compiles on every target and you want a runtime-looking boolean.
- If you still need to support a compiler older than 1.95, keep using the `cfg-if` crate until you raise the MSRV.
- Declare custom cfgs in `[lints.rust] unexpected_cfgs` so typos in predicates are caught.

## See Also

- [lint-cfg-check](lint-cfg-check.md) - declare known cfgs to catch typos in predicates
- [proj-msrv-declare](proj-msrv-declare.md) - declare and test the minimum supported Rust version
- [macro-prefer-functions](macro-prefer-functions.md) - reach for a macro only when a function cannot do the job
