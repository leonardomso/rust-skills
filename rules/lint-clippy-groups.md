# lint-clippy-groups

> Keep clippy's default groups on — `correctness` at deny; `suspicious`, `style`, `complexity`, and `perf` at warn — set them once in `[lints.clippy]`, and fail CI on their warnings

## Why It Matters

Clippy turns on five lint groups by default, and each catches a different class of problem. `correctness` flags code that is outright wrong. `suspicious` flags code that is very likely a bug. `style` flags code that isn't idiomatic, `complexity` flags code that could be simpler, and `perf` flags code that does needless work. All five are on by default, but warnings scroll past unless CI treats them as failures. Blanket `#![allow(clippy::all)]` attributes switch off the bug-finding groups along with the style ones. Writing the levels once in `Cargo.toml` makes them visible, applies them to every target, and keeps one place to change them.

## Bad

```rust
// lib.rs: blanket allows hide real bugs along with the noise
#![allow(clippy::all)]
#![allow(clippy::correctness)]

// CI: `cargo build` only, so clippy never runs
```

## Good

```toml
# Cargo.toml (or [workspace.lints.clippy] plus `[lints] workspace = true`)
[lints.clippy]
correctness = { level = "deny", priority = -1 }
suspicious  = { level = "warn", priority = -1 }
style       = { level = "warn", priority = -1 }
complexity  = { level = "warn", priority = -1 }
perf        = { level = "warn", priority = -1 }
```

```bash
# CI: run clippy on every target and fail on any warning from this workspace
CARGO_BUILD_WARNINGS=deny cargo clippy --all-targets --all-features
```

`priority = -1` lets individual lint entries in the same table override their group. Without it, clippy reports `lint_groups_priority`. Override a single lint for one item with `#[expect(clippy::lint, reason = "...")]`, not a blanket allow.

## What Each Group Catches

Group membership as of clippy 1.100; run `cargo clippy -- -W help` to list the current members.

| Group | Default | Catches | Examples |
|---|---|---|---|
| `correctness` | deny | Code that is wrong or does nothing | `eq_op` (`x == x`), `never_loop`, `iter_next_loop`, `absurd_extreme_comparisons`, `almost_swapped`, `suspicious_splitn`, `modulo_one` |
| `suspicious` | warn | Code that is very likely a bug | `await_holding_lock`, `suspicious_arithmetic_impl`, `suspicious_map`, `mutable_key_type`, `redundant_locals` |
| `style` | warn | Non-idiomatic code | `len_zero`, `needless_return`, `question_mark`, `single_match`, `ptr_arg`, `new_without_default`, `iter_nth` |
| `complexity` | warn | Code that could be simpler | `bind_instead_of_map`, `bool_comparison`, `clone_on_copy`, `filter_next`, `manual_flatten`, `needless_lifetimes`, `too_many_arguments` |
| `perf` | warn | Needless work or allocation | `manual_retain`, `iter_overeager_cloned`, `large_enum_variant`, `useless_vec`, `slow_vector_initialization`, `expect_fun_call` |

Before and after for a few of them:

```rust
// style::len_zero, style::question_mark, style::needless_return
fn first_even_before(v: &[i32]) -> Option<i32> {
    if v.len() == 0 {
        return None;
    }
    let first = match v.iter().find(|x| *x % 2 == 0) {
        Some(x) => x,
        None => return None,
    };
    return Some(*first);
}

fn first_even(v: &[i32]) -> Option<i32> {
    v.iter().copied().find(|x| x % 2 == 0)
}

// complexity::bind_instead_of_map, complexity::filter_next
fn bump(x: Option<i32>) -> Option<i32> {
    x.map(|n| n + 1) // not: x.and_then(|n| Some(n + 1))
}

fn first_long<'a>(words: &[&'a str]) -> Option<&'a str> {
    words.iter().copied().find(|w| w.len() > 3) // not: .filter(..).next()
}

// perf::manual_retain
fn keep_positive(mut v: Vec<i32>) -> Vec<i32> {
    v.retain(|x| *x > 0); // not: v.into_iter().filter(|x| *x > 0).collect()
    v
}
```

The groups that stay off by default (`pedantic`, `nursery`, `restriction`, `cargo`) are opinionated or noisy. Opt into individual lints from them instead of whole groups.

## See Also

- [lint-workspace-lints](lint-workspace-lints.md) - Configure lints once at the workspace level
- [lint-build-warnings](lint-build-warnings.md) - Deny warnings in CI with `build.warnings`
- [lint-expect-over-allow](lint-expect-over-allow.md) - Override a lint for one item with `#[expect]`
- [lint-pedantic-selective](lint-pedantic-selective.md) - Pick pedantic lints one by one
- [lint-clippy-nursery-selected](lint-clippy-nursery-selected.md) - Pick nursery lints one by one
- [lint-cargo-metadata](lint-cargo-metadata.md) - The `clippy::cargo` group for published crates
