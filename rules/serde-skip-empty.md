# serde-skip-empty

> Omit empty fields only when the wire contract equates empty and absent

## Why It Matters

`#[serde(skip_serializing_if = "predicate")]` can reduce payload size, but
missing, `null`, and empty often mean different things in PATCH requests,
configuration overlays, event schemas, and compatibility protocols. Use it
only when the versioned wire contract explicitly assigns the same meaning to
the omitted value. `#[serde(skip)]` removes a field from both directions and is
appropriate for internal state, not as an accidental compatibility change.

## Bad

```rust
use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize, Debug)]
struct ApiResponse {
    id: u64,
    name: String,
    description: Option<String>,  // serializes as null when None
    tags: Vec<String>,            // serializes as [] when empty
    error: Option<String>,        // serializes as null when None
}
```

Produces: `{"id":1,"name":"Alice","description":null,"tags":[],"error":null}`

## Good

```rust
use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize, Debug)]
struct ApiResponse {
    id: u64,
    name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    description: Option<String>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    tags: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
    // internal field excluded entirely from the wire format
    #[serde(skip)]
    _cache_key: Option<String>,
}

impl Default for ApiResponse {
    fn default() -> Self {
        ApiResponse {
            id: 0,
            name: String::new(),
            description: None,
            tags: Vec::new(),
            error: None,
            _cache_key: None,
        }
    }
}
```

Produces: `{"id":1,"name":"Alice"}` — absent fields are simply omitted.

## Key Points

- `skip_serializing_if` takes any path resolving to `fn(&T) -> bool`. Common choices:
  - `Option::is_none` for `Option<T>`
  - `Vec::is_empty` / `<[T]>::is_empty` for collections
  - `String::is_empty` for strings
  - A custom function for more complex conditions
- `#[serde(skip)]` removes the field from **both** directions. The type must implement `Default` so deserialization can still construct the struct (serde fills it with `Default::default()`).
- `#[serde(skip_serializing)]` skips only on the way out; `#[serde(skip_deserializing)]` skips only on the way in — useful when reading legacy fields you no longer write.
- Pair `skip_serializing_if` with `#[serde(default)]` only when missing input is
  defined to produce that default. Otherwise require the field so omission
  fails closed.

## See Also

- [serde-default-compat](serde-default-compat.md) - fill missing fields from Default on deserialization
- [serde-rename-all](serde-rename-all.md) - match external naming conventions with rename_all
