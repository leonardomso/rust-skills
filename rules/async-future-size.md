# async-future-size

> Keep frequently created futures small by dropping large setup state before the first suspension point

## Why It Matters

Arguments and locals that remain live across `.await` are candidates for
storage in the generated state machine, subject to compiler layout
optimization. Tokio commonly stores a spawned future in one task allocation
and polls it in place; that is a runtime implementation strategy, not a Rust
language guarantee. Large future values can increase task storage, cache
pressure, and movement before pinning. Measure hot entry points and keep large,
rare state out of the common future type.

## Bad

```rust
pub struct Payload([u8; 4096]);

pub async fn first_byte(payload: Payload) -> u8 {
    std::future::ready(()).await;
    payload.0[0]
}
```

The entire payload remains part of the future because it is read after the
suspension point.

## Good

```rust
use std::future::Future;

pub struct Payload([u8; 4096]);

pub fn first_byte(payload: Payload) -> impl Future<Output = u8> {
    let first = payload.0[0];
    // `payload` is dropped before the returned future is created.
    async move {
        std::future::ready(()).await;
        first
    }
}

#[test]
fn hot_future_size_is_bounded() {
    let future = first_byte(Payload([7; 4096]));
    assert!(std::mem::size_of_val(&future) <= 16);
}

fn main() {
    let _ = first_byte(Payload([7; 4096]));
}
```

A size assertion is useful only for a measured hot path. Treat the threshold as
an architecture-specific regression budget, not a universal ABI guarantee.

## Key Points

- Inspect values that remain live across each `.await`; source order alone does
  not determine liveness.
- Extract small required data before constructing the async block when setup is
  synchronous.
- Box a genuinely rare large branch when reducing the common future outweighs
  one allocation on that branch.
- Use `clippy::large_futures` as a tripwire, then profile before reshaping code.
- Move sustained CPU work to a bounded compute pool; shrinking a future does
  not make CPU work cooperative.
- Recheck thresholds after compiler or target changes because state-machine
  layout is not a stable interface.

## See Also

- [mem-assert-type-size](mem-assert-type-size.md) - measured size regression budgets
- [async-fn-over-future](async-fn-over-future.md) - return `impl Future` only when setup or bounds require it
- [async-spawn-blocking](async-spawn-blocking.md) - isolate sustained CPU work
- [perf-profile-first](perf-profile-first.md) - optimize measured hot paths
