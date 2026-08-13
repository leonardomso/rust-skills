# doc-no-meta-design

> Document the shipped crate for users; keep design history and process notes out of rustdoc

## Why It Matters

Callers open crate and module docs to learn what the type does *now* — arguments, failure modes, invariants. Keep that surface free of the story of how the crate was built. Agents in particular paste design journals, "we chose X after trying Y" essays, and self-scorecards of which rules they followed. Those notes help the author during the change and then rot. They do not explain behavior. Put the working record in a PR, an ADR, or an internal log; put the finished contract in rustdoc.

## Bad

```rust
//! # invoice-total
//!
//! ## How this was designed
//! First pass used a visitor. The borrow checker pushed us to a
//! fold. We then renamed every helper to satisfy an internal checklist.
//!
//! ## Agent report
//! | Check | Done | Notes |
//! | ----- | ---- | ----- |
//! | short names | yes | renamed `compute_sum_of_line_items` |
//! | display impls | yes | added `Display` on `Money` |

pub fn total_cents(lines: &[u32]) -> u32 {
    lines.iter().copied().sum()
}
```

## Good

```rust
//! Sums invoice line amounts in cents.
//!
//! Pass the line items in document order. The result is the wrapping
//! sum of those amounts with explicit wrapping arithmetic.

/// Adds every line amount in cents.
pub fn total_cents(lines: &[u32]) -> u32 {
    lines
        .iter()
        .copied()
        .fold(0, u32::wrapping_add)
}

fn main() {
    assert_eq!(total_cents(&[150, 250]), 400);
}
```

## Key Points

- User-facing crate and module docs describe the end state: what to call, what it returns, what can fail.
- Design history, discarded alternatives, and "which guidelines we applied" tables belong in review artifacts, not in rustdoc.
- Process prose goes stale the next time the code changes; behavior docs are what users re-read.
- A short **Design Principles** (or equivalent) section in the README is allowed when it states *enduring* goals a user must know — the crate is `no_std`, the scan path does not allocate, I/O sits behind a narrow trait. That is product shape, not a diary of the last refactor.

## Design Principles Carve-Out

A README section that names lasting product constraints is for users. A section that recounts the last three refactors is not.

````markdown
## Design Principles

- The scan path does not allocate.
- The crate builds with `no_std` plus `alloc`.
- I/O is behind a small trait; the core types do not open sockets.
````

## See Also

- [doc-crate-readme](doc-crate-readme.md) - the README is the user-facing front page; keep it current, not autobiographical
- [doc-module-inner](doc-module-inner.md) - `//!` describes the module as shipped
- [doc-all-public](doc-all-public.md) - public items still need behavior comments
- [doc-first-sentence](doc-first-sentence.md) - the first sentence is a user summary, not a design recap
