# async-fn-in-trait

> Use native `async fn` in traits (stable 1.75) instead of the `async_trait` macro

## Why It Matters

Since Rust 1.75, you can write `async fn` directly inside trait definitions (AFIT — async functions in traits). This eliminates the `#[async_trait]` proc-macro dependency and removes the hidden `Box<dyn Future>` allocation it inserts on every call. Fewer allocations, no macro expansion overhead, and no extra crate to audit. Before migrating, know its two caveats: such traits are not dyn-compatible, and their futures are not guaranteed to be `Send`.

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

**Caveat 1: not dyn-compatible.** A trait with a native `async fn` is not dyn-compatible (object-safe), because each method returns an opaque `impl Future`. You cannot write `Box<dyn Repo>` with the definition above. Dynamic dispatch needs the future type erased into a `Pin<Box<dyn Future>>`. You can do that in two ways:

- Keep `#[async_trait]` for traits used as `dyn Trait`. It boxes every returned future.
- Write a small boxed-future adapter trait by hand and blanket-implement it for every type that implements the native trait. Callers that know the concrete type still get the unboxed version.

```rust
use std::future::Future;
use std::pin::Pin;

// native trait; `+ Send` on the future lets the adapter below box it as Send
trait Repo: Send + Sync {
    fn get(&self, id: u64) -> impl Future<Output = anyhow::Result<String>> + Send;
}

// dyn-compatible twin: the future is type-erased and boxed
trait DynRepo: Send + Sync {
    fn get(&self, id: u64) -> Pin<Box<dyn Future<Output = anyhow::Result<String>> + Send + '_>>;
}

impl<T: Repo> DynRepo for T {
    fn get(&self, id: u64) -> Pin<Box<dyn Future<Output = anyhow::Result<String>> + Send + '_>> {
        Box::pin(Repo::get(self, id))
    }
}

struct PgRepo;

impl Repo for PgRepo {
    async fn get(&self, id: u64) -> anyhow::Result<String> {
        Ok(format!("row-{id}"))
    }
}

fn make_repo() -> Box<dyn DynRepo> {
    Box::new(PgRepo) // generic code can still use `Repo` directly, unboxed
}
```

The `trait-variant` crate does **not** make a trait dyn-compatible. `#[trait_variant::make(RepoSend: Send)]` generates a `RepoSend` whose methods return `impl Future<Output = _> + Send`. That fixes `Send` (Caveat 2), but the return type is still opaque, so `Box<dyn RepoSend>` is rejected just like `Box<dyn Repo>`. Being `Send` and being dyn-compatible are separate properties.

**Caveat 2: futures are not `Send` by default.** On a multi-threaded Tokio runtime, spawned tasks need `Send` futures. A generic caller can't tell whether the future from a native `async fn` in a trait is `Send`. If you need `Send`, either:

- Use `#[trait_variant::make(TraitNameSend: Send)]` from the `trait-variant` crate to generate a `Send`-bounded variant for static dispatch.
- Write the method in desugared form with an explicit bound: `fn get(&self, id: u64) -> impl Future<Output = anyhow::Result<String>> + Send`.

```rust
use std::future::Future;

// explicit Send bound on the returned future
trait Repo {
    fn get(&self, id: u64) -> impl Future<Output = anyhow::Result<String>> + Send;
}

struct PgRepo;

impl Repo for PgRepo {
    // implementors can still write `async fn`
    async fn get(&self, id: u64) -> anyhow::Result<String> {
        Ok(format!("row-{id}"))
    }
}

fn spawn_get<R: Repo + Send + Sync + 'static>(repo: std::sync::Arc<R>) {
    tokio::spawn(async move { repo.get(1).await });
}
```

## When to Use Each Approach

| Scenario | Recommended approach |
|---|---|
| Static dispatch only (generics, `impl Trait`) | Native `async fn` in trait |
| Need `dyn Trait` | `#[async_trait]`, or a hand-written boxed-future adapter trait |
| Multi-threaded Tokio, spawned tasks, static dispatch | `trait-variant` `Send` variant or explicit `-> impl Future + Send` |
| Multi-threaded Tokio **and** `dyn Trait` | `#[async_trait]` (boxes futures as `Send` by default) |
| Single-threaded runtime / `LocalSet` | Native `async fn` in trait (no `Send` needed) |

## See Also

- [trait-dyn-vs-generic](trait-dyn-vs-generic.md) - prefer `impl Trait` over `Box<dyn Trait>` when possible
- [async-async-fn-bounds](async-async-fn-bounds.md) - use `AsyncFn` bounds for higher-order async functions
- [async-tokio-runtime](async-tokio-runtime.md) - use Tokio for production async runtime
