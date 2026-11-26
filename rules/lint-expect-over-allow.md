# lint-expect-over-allow

> Use `#[expect(lint, reason = "...")]` instead of `#[allow]` when overriding a lint for one item

## Why It Matters

An `#[allow]` stays in the code forever, even after the code it excused is fixed or deleted. `#[expect]` (stable since Rust 1.81) does the same job, but warns when the lint no longer fires, so stale overrides get removed. The `reason` string tells a reviewer why the exception exists. Keep `#[allow]` for generated code and macro output, where the lint may fire in some expansions and not in others.

## Bad

```rust
// Never revisited, even if the function starts using I/O
#[allow(clippy::unused_async)]
pub async fn ping_server() {}

#[allow(dead_code)]
fn helper() {}
```

## Good

```rust
#[expect(clippy::unused_async, reason = "signature is fixed; I/O arrives later")]
pub async fn ping_server() {}

#[expect(dead_code, reason = "used by the upcoming importer")]
fn helper() {}
```

## Notes

- If an `#[expect]` stops matching, the compiler reports `unfulfilled_lint_expectations`. Delete the attribute.
- Project-wide lint levels belong in `[lints]` in `Cargo.toml`, not in scattered attributes. See [lint-workspace-lints](lint-workspace-lints.md).

## See Also

- [lint-workspace-lints](lint-workspace-lints.md) - Configure lints in one place
- [lint-warn-style](lint-warn-style.md) - Enable clippy style lints
- [lint-pedantic-selective](lint-pedantic-selective.md) - Choose pedantic lints deliberately
- Source: Microsoft Pragmatic Rust Guidelines, M-LINT-OVERRIDE-EXPECT
