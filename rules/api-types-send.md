# api-types-send

> Make public types and the futures they produce `Send`, and assert it so it stays that way

## Why It Matters

Work-stealing runtimes such as Tokio need spawned futures to be `Send`. A single `Rc` or `RefCell` held across an `.await` inside your library makes the caller's whole future `!Send`, and the error shows up in their code, not yours. Making types `Send` costs little unless you touch atomics in a tight loop. A type that is only used for an instant, such as a telemetry ping that is never held across an await, may reasonably stay `!Send`.

## Bad

```rust
use std::cell::RefCell;
use std::collections::HashMap;
use std::rc::Rc;

pub struct Cache {
    // Rc makes Cache !Send, so any future holding a Cache is !Send too
    entries: Rc<RefCell<HashMap<String, String>>>,
}
```

## Good

```rust
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

#[derive(Clone, Default)]
pub struct Cache {
    entries: Arc<Mutex<HashMap<String, String>>>,
}

impl Cache {
    pub async fn get(&self, key: &str) -> Option<String> {
        tokio::task::yield_now().await;
        self.entries.lock().ok()?.get(key).cloned()
    }
}

// Compile-time guard: fails to build if Cache ever stops being Send + Sync
const fn assert_send_sync<T: Send + Sync>() {}
const _: () = assert_send_sync::<Cache>();

#[cfg(test)]
mod tests {
    use super::*;

    fn assert_send<T: Send>(_: T) {}

    #[test]
    fn futures_are_send() {
        let cache = Cache::default();
        assert_send(cache.get("key"));
    }
}
```

## See Also

- [unsafe-send-sync-manual](unsafe-send-sync-manual.md) - Never force `Send` with an unsafe impl
- [own-arc-shared](own-arc-shared.md) - `Arc` for shared ownership across threads
- [own-rc-single-thread](own-rc-single-thread.md) - Why `Rc` is `!Send`
- [async-no-lock-await](async-no-lock-await.md) - Do not hold guards across await points
- Source: Microsoft Pragmatic Rust Guidelines, M-TYPES-SEND
