# macro-no-rewrite-item

> Do not let a macro change an item's kind, signature, or async-ness from what the source shows

## Why It Matters

Readers and agents trust that `fn tally()` is a synchronous function with that arity. A macro that injects arguments or turns the item `async` makes every call site look wrong until you expand it. Treat that as lying about the signature: generate repetitive tokens, but leave the written shape of the item intact.

## Bad

```rust
// Imagined attribute: adds a `token` argument and makes the function async.
// Callers then write `tally(token).await` next to a source line that says `fn tally()`.
fn tally() {}

fn main() {
    tally();
}
```

## Good

```rust
macro_rules! ready_ok {
    ($ty:ty) => {{
        async { Result::<$ty, &'static str>::Ok(<$ty>::default()) }
    }};
}

async fn fetch_count() -> Result<u32, &'static str> {
    ready_ok!(u32).await
}

fn main() {
    let _ = fetch_count;
}
```

## See Also

- [macro-prefer-functions](macro-prefer-functions.md) - if the shape is a function, write a function
- [macro-rules-hygiene](macro-rules-hygiene.md) - expand into the tokens a reader already expects
- [macro-proc-error-spans](macro-proc-error-spans.md) - if a rewrite is unavoidable, fail at the caller's span
