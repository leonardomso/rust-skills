# obs-structured-fields

> Record structured key-value fields, not values interpolated into the message string

## Why It Matters

When values are interpolated directly into the message string (e.g., `"processed 42 items for user 7 in 120ms"`), they become opaque text. Log aggregators (Loki, Elasticsearch, OpenTelemetry) cannot filter on `items = 42` or group by `user.id` because those values no longer exist as discrete fields. Structured fields keep data machine-parseable, filterable, and chart-able without regex post-processing. `tracing` supports three field sigils: `%expr` for `Display`, `?expr` for `Debug`, and bare `field = value` for typed primitives — the message string should only contain a stable, human-readable description.

## Bad

```rust
use tracing::info;

fn process_batch(user_id: u64, items: usize, elapsed_ms: u64) {
    // Values buried in the message string — unqueryable in aggregators
    info!("processed {} items for user {} in {}ms", items, user_id, elapsed_ms);
}
```

## Good

```rust
use tracing::info;

fn process_batch(user_id: u64, items: usize, elapsed_ms: u64) {
    // Structured: each value is a discrete, queryable field
    info!(
        user.id = user_id,
        items,
        elapsed_ms,
        "batch processed"
    );
}

#[derive(Debug)]
struct Request {
    path: String,
    method: String,
}

fn handle_request(req: &Request, status: u16) {
    // %req uses Display; ?req uses Debug; status is a primitive
    info!(
        request = ?req,   // Debug format for the whole struct
        status,
        "request complete"
    );
}
```

## Field Sigil Reference

| Syntax | Trait used | When to use |
|---|---|---|
| `field = value` | native (primitive) | integers, bools, floats |
| `field = %expr` | `Display` | strings, IDs, URLs, types with clean `Display` |
| `field = ?expr` | `Debug` | structs, enums, vecs — for diagnostics |
| `field` (shorthand) | same as `field = field` | when name matches variable |

## Key Points

- Keep the message string short and stable. If the telemetry backend supports message templates, reference the structured field names rather than formatting their values eagerly.
- Prefer `%` over `?` for values that have a clean `Display` (e.g., `%id`, `%path`) — JSON backends quote Debug output inconsistently.
- Use namespaced field names like `user.id`, `http.status`, `db.query` when aligning to OpenTelemetry semantic conventions.
- Record each value once as a field. A template placeholder that names that field is metadata, not a second serialized copy.

## See Also

- [obs-tracing-over-log](obs-tracing-over-log.md) - foundational setup for `tracing`
- [obs-no-sensitive-data](obs-no-sensitive-data.md) - never put secrets or PII in structured fields
- [obs-error-chain](obs-error-chain.md) - log errors as structured fields with full source chain
- [obs-named-events](obs-named-events.md) - give the event a stable name, not only fields
