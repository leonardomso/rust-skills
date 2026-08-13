# lint-expect-override

> Prefer `#[expect(...)]` over `#[allow(...)]` when silencing a lint at an item

## Why It Matters

`#[allow]` stays quiet even after the lint no longer fires, so overrides pile up as cargo-cult comments. `#[expect]` warns once the lint is gone, so the override cannot outlive the code that needed it unnoticed. Pair every override with a `reason` so reviewers can tell whether the exception is still load-bearing.

## Bad

```rust
#[allow(clippy::unused_async)]
pub async fn flush_metrics() {
    // The allow will linger after this function starts writing I/O.
}
```

## Good

```rust
#[expect(clippy::unused_async, reason = "signature is fixed; body will flush to the socket")]
pub async fn flush_metrics() {
    // Body still empty; expect fires once the lint stops applying.
}

fn main() {
    let _ = flush_metrics;
}
```

## When `#[allow]` Is Still Right

Keep `#[allow]` for generated code and for macros that expand into many sites you do not control. Those expansions can stop triggering a lint without anyone editing the attribute, so an `#[expect]` would become a false failure.

## See Also

- [lint-workspace-lints](lint-workspace-lints.md) - set the default lint level once, then override locally
- [lint-clippy-nursery-selected](lint-clippy-nursery-selected.md) - enable extra lints only where they pay off
- [unsafe-safety-comment](unsafe-safety-comment.md) - document why an exception exists, not only that it exists
