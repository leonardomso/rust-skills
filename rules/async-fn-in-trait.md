# async-fn-in-trait

> Use native async trait methods for static dispatch; box futures deliberately for `dyn`

## Why It Matters

Since Rust 1.75, a trait can declare `async fn` directly. Static dispatch then
uses an opaque concrete future without requiring `async_trait`'s box. The
method body can still allocate for other reasons. Public traits must decide
future bounds such as `Send` up front, and native async methods are not
dyn-compatible. Choose from the substitution and ownership contract rather
than applying a blanket migration.

## Bad

```rust
// requires async_trait crate; boxes every future on the heap
use async_trait::async_trait;

#[async_trait]
trait Repo {
    async fn get(&self, id: u64) -> anyhow::Result<String>;
    async fn save(&self, value: String) -> anyhow::Result<()>;
}

struct PgRepo;

#[async_trait]
impl Repo for PgRepo {
    async fn get(&self, id: u64) -> anyhow::Result<String> {
        Ok(format!("row-{id}"))
    }

    async fn save(&self, value: String) -> anyhow::Result<()> {
        let _ = value;
        Ok(())
    }
}
```

## Good

```rust
// native async fn in traits — no macro, no boxing
trait Repo {
    async fn get(&self, id: u64) -> anyhow::Result<String>;
    async fn save(&self, value: String) -> anyhow::Result<()>;
}

struct PgRepo;

impl Repo for PgRepo {
    async fn get(&self, id: u64) -> anyhow::Result<String> {
        Ok(format!("row-{id}"))
    }

    async fn save(&self, value: String) -> anyhow::Result<()> {
        let _ = value;
        Ok(())
    }
}
```

## Caveats

**Caveat 1 — not dyn-compatible.** Native async fn in traits is not
dyn-compatible. You cannot write `Box<dyn Repo>` with the definition above.
For dynamic dispatch:

- Keep `#[async_trait]` (it boxes the future, which makes the trait object-safe).
- Or write an object-safe method that returns
  `Pin<Box<dyn Future<Output = T> + Send + '_>>` explicitly.

```rust
use std::{future::Future, pin::Pin};

trait DynRepo {
    fn get(
        &self,
        id: u64,
    ) -> Pin<Box<dyn Future<Output = anyhow::Result<String>> + Send + '_>>;
}

fn make_repo() -> Box<dyn DynRepo> {
    // ...
    # unimplemented!()
}
```

`trait-variant` generates a second trait with stronger future bounds; it does
not make that trait dyn-compatible.

**Caveat 2 — the trait does not promise `Send`.** A concrete implementation's
generated future may be `Send`, but a native async trait method does not let
generic callers require that property from the trait declaration. Multi-thread
`tokio::spawn` requires a `Send + 'static` future. If callers need that
guarantee:

- Use `#[trait_variant::make(TraitNameSend: Send)]` from the `trait-variant` crate to generate a `Send`-bounded variant.
- Bound the return type explicitly: `fn get(&self, id: u64) -> impl Future<Output = anyhow::Result<String>> + Send`.

```rust
// explicit Send bound on the return future
trait Repo {
    fn get(&self, id: u64) -> impl Future<Output = anyhow::Result<String>> + Send;
}
```

## When to Use Each Approach

| Scenario | Recommended approach |
|---|---|
| Static dispatch only (generics, `impl Trait`) | Native `async fn` in trait |
| Need `dyn Trait` | `#[async_trait]` or an explicit boxed-future method |
| Multi-threaded Tokio, spawned tasks | `trait-variant` `Send` variant or explicit `+ Send` |
| Single-threaded runtime / `LocalSet` | Native `async fn` in trait (no `Send` needed) |

## See Also

- [anti-type-erasure](anti-type-erasure.md) - prefer `impl Trait` over `Box<dyn Trait>` when possible
- [async-async-fn-bounds](async-async-fn-bounds.md) - use `AsyncFn` bounds for higher-order async functions
- [async-tokio-runtime](async-tokio-runtime.md) - use Tokio for production async runtime
