# async-future-size

> Track the size of futures on hot paths and keep large values out of their state machines

## Why It Matters

An `async fn` compiles to a state machine. Its arguments and every local that lives across an `.await` are stored inside it, so a large argument or buffer makes every future of that type large. Big futures cost memcpy work when they are created, moved, boxed, or spawned, and they inflate the size of any future that awaits them. This only matters for functions called very often or spawned in large numbers, so measure first and fix the hot ones.

## Bad

```rust
// The 16 KiB array is a parameter, so it lives inside the future
async fn handle(buf: [u8; 16 * 1024]) -> usize {
    tokio::task::yield_now().await;
    buf.iter().filter(|&&b| b == b'\n').count()
}
```

## Good

```rust
use std::future::Future;

// Do the synchronous work before the async block; only the result is captured
fn handle(raw: &[u8]) -> impl Future<Output = usize> + use<> {
    let lines = raw.iter().filter(|&&b| b == b'\n').count();
    async move {
        tokio::task::yield_now().await;
        lines
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn handle_future_stays_small() {
        let fut = handle(b"a\nb\n");
        // Pick the limit from the first measurement, then guard against growth
        assert!(std::mem::size_of_val(&fut) <= 64);
    }
}
```

## Ways to Shrink a Future

- Pass large inputs by reference or as `Box<T>`/`Vec<T>` instead of by value.
- Drop big locals (or end their scope) before the next `.await`. A value with a destructor stays alive until the end of its scope.
- Move synchronous setup out of the `async` body, as above.
- Box a rarely used, large sub-future so it does not widen the common case.

## See Also

- [mem-assert-type-size](mem-assert-type-size.md) - Guard type sizes with static assertions
- [mem-box-large-variant](mem-box-large-variant.md) - Box large variants to shrink the whole
- [own-move-large](own-move-large.md) - Moving large values is not free
- [async-clone-before-await](async-clone-before-await.md) - What to hold across await points
- Source: Microsoft Pragmatic Rust Guidelines, M-ASYNC-STACK-SIZE
