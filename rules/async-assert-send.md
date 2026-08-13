# async-assert-send

> Assert that public futures and handles are `Send` so they can move across Tokio workers

## Why It Matters

A public `async fn` that holds `Rc` or a `!Send` guard across `.await` compiles until a caller writes `tokio::spawn`. The error then appears in *their* crate. Public futures and handles intended to cross workers should stay `Send`. A compile-time `require_send` next to each main entry point fails in *your* crate the moment a field or capture regresses. Do not assert every helper mechanically. An instantaneous `!Send` temporary is fine when it is created, used, and dropped before any `.await`.

## Bad

```rust
use std::rc::Rc;

pub async fn fetch_blob(name: &str) {
    let _keep = Rc::new(name.to_string());
    async { let _ = name; }.await;
}

// Compiles here. `tokio::spawn(fetch_blob("x"))` fails in the caller.
```

## Good

```rust
use std::future::Future;
use std::pin::Pin;
use std::sync::Arc;
use std::task::{Context, Poll};

pub struct BlobRead {
    _buf: Arc<[u8]>,
}

impl Future for BlobRead {
    type Output = usize;

    fn poll(self: Pin<&mut Self>, _: &mut Context<'_>) -> Poll<Self::Output> {
        Poll::Ready(0)
    }
}

const fn require_send<T: Send>() {}
const _: () = require_send::<BlobRead>();

pub async fn fetch_blob(name: Arc<str>) {
    let length = {
        let local = std::rc::Rc::new(name.len());
        *local
    }; // `!Send` state leaves scope before the await below.
    std::future::ready(()).await;
    let _ = (name, length);
}

fn require_future_send<T: Send>(_: &T) {}

fn main() {
    let fut = fetch_blob(Arc::from("notes.txt"));
    require_future_send(&fut);
}
```

## See Also

- [async-clone-before-await](async-clone-before-await.md) - drop `!Send` borrows before the future is spawned
- [own-arc-shared](own-arc-shared.md) - `Arc<T>` can cross threads only when `T` permits it
- [unsafe-send-sync-manual](unsafe-send-sync-manual.md) - do not paper over a `!Send` field with an unsafe impl
