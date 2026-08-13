# async-fn-over-future

> Prefer `async fn` for readability; return `impl Future` when bounds or capture are the contract

## Why It Matters

`async fn foo()` and `fn foo() -> impl Future` can describe the same work. The `async fn` form is the idiomatic public signature: readers do not have to decode a return-position future, and the body does not need an extra `async` block. Keep that as the default whenever both are viable. Write an explicit `Future`-returning signature only when the `async fn` desugaring cannot express the bound or capture you need.

## Bad

```rust
use std::future::Future;

struct Foo;

impl Foo {
    // Bad, signature is noisier and the body needs an extra `async` block
    fn foo() -> impl Future<Output = Result<u32, FooError>> {
        async { Ok(1) }
    }
}

pub struct FooError;
```

## Good

```rust
struct Foo;

impl Foo {
    // Good, method and implementation reads normally
    async fn foo() -> Result<u32, FooError> {
        Ok(1)
    }
}

pub struct FooError;
```

## When to Return `impl Future`

Use an explicit future type only for these cases:

**`Send` (or other) bounds.** A native `async fn` signature does not spell out
an auto-trait promise on its generated future. When callers must be able to
`tokio::spawn` the result across future implementation changes, return
`impl Future + Send` and test that contract. This applies to traits and to
public free/inherent functions (`async-fn-in-trait`, `async-assert-send`).

```rust
use std::future::Future;

pub trait Repo {
    fn get(&self, id: u64) -> impl Future<Output = Result<String, RepoError>> + Send;
}

pub struct RepoError;
```

**Intentionally controlling future size, capture, or type.** Hot, frequently instantiated async work should not drag large arguments or setup locals into the state machine. Returning `impl Future` lets you run that setup *outside* `async {}`, pick `Either` for early-error branches, and keep `size_of_val(&fut)` small (`async-future-size`).

```rust
use std::future::Future;

pub struct SetupData(Box<[u8; 32 * 1024]>);

pub fn send(payload: SetupData) -> impl Future<Output = usize> + Send {
    let first = payload.0[0];
    async move {
        std::future::ready(()).await;
        first as usize
    }
}
```

Ordinary public API methods are not in that set. Do not return `impl Future` for taste, "flexibility," or to hide an `async` keyword. Higher-order callbacks use `AsyncFn` bounds (`async-async-fn-bounds`); they are not a reason to avoid `async fn` on the method itself.

## See Also

- [async-future-size](async-future-size.md) - the hot-path exception: extract setup and return `impl Future`
- [async-fn-in-trait](async-fn-in-trait.md) - native `async fn` in traits, and when you must name the future for `Send` or `dyn`
- [async-assert-send](async-assert-send.md) - public futures still have to be `Send` on a multi-thread runtime
- [async-async-fn-bounds](async-async-fn-bounds.md) - `AsyncFn` for parameters that *are* futures, not for the method you are writing
