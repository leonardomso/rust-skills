# obs-log-overhead

> Keep telemetry on hot paths cheap: no allocation per event and no per-item events in inner loops

## Why It Matters

A library cannot know how its users configure logging. Assume events are always on and the system is under load. Building a string with `format!` for every item allocates even when the event is later filtered out, and one event per item in a tight loop can dominate the real work. Record structured fields, which cost nothing when the level is disabled, and emit one summary event per batch instead.

## Bad

```rust
use tracing::debug;

fn send_all(ids: &[u64]) {
    for id in ids {
        // Allocates a String for every item, even if debug is disabled
        debug!("{}", format!("sending message {id}"));
        send(*id);
    }
}

fn send(_id: u64) {}
```

## Good

```rust
use tracing::{debug, trace};

fn send_all(batch_id: u64, ids: &[u64]) {
    // One event for the whole batch; consumers can reconstruct the rest
    debug!(batch_id, count = ids.len(), "sending batch");
    for id in ids {
        // Fields are only evaluated if trace is enabled; no string building
        trace!(id, "sending message");
        send(*id);
    }
}

fn send(_id: u64) {}
```

## See Also

- [obs-structured-fields](obs-structured-fields.md) - Fields instead of interpolated strings
- [obs-levels-filter](obs-levels-filter.md) - Pick levels so noisy events are off by default
- [anti-format-hot-path](anti-format-hot-path.md) - Avoid `format!` in hot paths
- [obs-library-facade](obs-library-facade.md) - Libraries only emit events
- Source: Microsoft Pragmatic Rust Guidelines, M-LOG-OVERHEAD
