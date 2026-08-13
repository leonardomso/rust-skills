# doc-first-sentence

> Write the first rustdoc sentence as one short standalone line — about fifteen words — that still makes sense in the module index

## Why It Matters

`cargo doc` lifts the first sentence into the module summary. A clause that only works after the next paragraph, or a line that wraps twice, becomes an unreadable index. Keeping that sentence to roughly fifteen words usually preserves a one-line summary at the default rustdoc width. `clippy::too_long_first_doc_paragraph` flags the wrapping case; this rule is the editorial half: one sentence, one idea, no "this function..." throat-clearing.

## Bad

```rust
/// This helper, which you will typically call after constructing a `Client` and
/// before the first request, prepares the connection pool so that subsequent
/// calls do not pay the setup cost again.
pub fn warmup() {}
```

## Good

```rust
/// Prepares the client connection pool for the first request.
///
/// Call after `Client::new` and before the first RPC. Skipping it is safe
/// but the first call then pays setup latency.
pub fn warmup() {}

fn main() {
    warmup();
}
```

## See Also

- [doc-all-public](doc-all-public.md) - every public item still needs a full comment
- [doc-module-inner](doc-module-inner.md) - the same first-sentence rule applies to `//!` module docs
- [lint-missing-docs](lint-missing-docs.md) - `missing_docs` catches absence; this rule catches a useless first line
