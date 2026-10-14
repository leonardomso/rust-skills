# async-fn-in-trait

> Use native `async fn` in traits (stable 1.75) instead of the `async_trait` macro

## Why It Matters

Since Rust 1.75, you can write `async fn` directly inside trait definitions (AFIT — async functions in traits). This eliminates the `#[async_trait]` proc-macro dependency and removes the hidden `Box<dyn Future>` allocation it inserts on every call. Fewer allocations, no macro expansion overhead, and no extra crate to audit. However, native async fn in traits carries two precise caveats you must understand before migrating.

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

**Caveat 1 — not dyn-compatible.** Native async fn in traits is not dyn-compatible. You cannot write `Box<dyn Repo>` with the definition above. For dynamic dispatch, use `#[async_trait]` on the trait and its implementations to box the returned futures.

The `trait-variant` macro adds `Send` bounds to the generated trait and its returned futures for static dispatch. It does not box those futures or make the generated async-method variant dyn-compatible.

```rust
// using async-trait for a dyn-compatible trait
#[async_trait::async_trait]
trait Repo {
    async fn get(&self, id: u64) -> anyhow::Result<String>;
}

// async-trait boxes the future returned by `get`, allowing `dyn Repo`
fn make_repo() -> Box<dyn Repo> {
    // ...
    # unimplemented!()
}
```

**Caveat 2 — futures are not `Send` by default.** On a multi-threaded Tokio runtime, spawned tasks require `Send` futures. The auto-generated future from a native `async fn` in a trait captures `&self` but does not promise `Send`. If you need `Send`, either:

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
| Need `dyn Trait` | `#[async_trait]` |
| Multi-threaded Tokio, spawned tasks | `trait-variant` `Send` variant or explicit `+ Send` |
| Single-threaded runtime / `LocalSet` | Native `async fn` in trait (no `Send` needed) |

## See Also

- [anti-type-erasure](anti-type-erasure.md) - prefer `impl Trait` over `Box<dyn Trait>` when possible
- [async-async-fn-bounds](async-async-fn-bounds.md) - use `AsyncFn` bounds for higher-order async functions
- [async-tokio-runtime](async-tokio-runtime.md) - use Tokio for production async runtime
