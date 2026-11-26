# lint-clippy-nursery-selected

> Enable high-value `clippy::nursery` lints selectively, not the whole group

## Why It Matters

The `clippy::nursery` group contains lints that are correct and useful but still being refined — their suggestions may be noisy or have edge cases that haven't been polished yet. Enabling the entire group (`#![warn(clippy::nursery)]`) floods you with false positives and creates churn as nursery lints graduate or change. Cherry-picking individual lints gives you the signal without the noise. Several nursery lints are especially valuable: `significant_drop_tightening` catches lock guards held longer than necessary (use `clippy::await_holding_lock` for guards held across `.await`), `redundant_clone` flags clones that could be moves, and `use_self` keeps type names DRY inside impl blocks.

## Bad

```toml
# Cargo.toml — enables every nursery lint, including noisy ones
[lints.clippy]
nursery = "warn"
```

## Good

```toml
# Cargo.toml — selectively enable high-value nursery lints
[lints.clippy]
# Catches lock/guard held longer than necessary
significant_drop_tightening = "warn"
# Flags .clone() calls that could be avoided by moving
redundant_clone = "warn"
# Replace TypeName with Self inside impl blocks
use_self = "warn"
# Branches of an if/match that start or end with the same code
branches_sharing_code = "warn"
# Avoid eagerly evaluating function calls in unwrap_or / or / map_or
or_fun_call = "warn"
```

```rust
// significant_drop_tightening example — lint fires here:
fn process(state: &Mutex<Vec<u32>>) -> usize {
    let guard = state.lock().unwrap();
    let len = guard.len();
    drop(guard);          // lint suggests dropping earlier, before the return
    expensive_work();
    len
}

// use_self example — lint fires here:
impl MyStruct {
    fn new() -> MyStruct {   // should be -> Self
        MyStruct { value: 0 }
    }
}

// Correct:
impl MyStruct {
    fn new() -> Self {
        Self { value: 0 }
    }
}
```

## Suggested Starter Set

| Lint | What it catches |
|------|----------------|
| `significant_drop_tightening` | Guards/locks held longer than needed |
| `redundant_clone` | `.clone()` where a move suffices |
| `use_self` | Type name repeated inside `impl` block |
| `branches_sharing_code` | Identical code at the start or end of every branch |
| `or_fun_call` | `unwrap_or(expensive())` → `unwrap_or_else(expensive)` |

Start with this set. Add more only after reviewing what they flag in your codebase.

## See Also

- [lint-pedantic-selective](lint-pedantic-selective.md) - same strategy for clippy::pedantic
- [lint-warn-perf](lint-warn-perf.md) - enable the performance lint group
- [anti-lock-across-await](anti-lock-across-await.md) - don't hold locks across `.await`
