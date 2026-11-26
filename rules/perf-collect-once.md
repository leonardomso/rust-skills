# perf-collect-once

> Chain iterator adapters and collect once at the end, or not at all

## Why It Matters

Each `.collect()` allocates a new collection and ends the lazy pipeline, so a chain with intermediate collections costs extra memory, extra passes, and lost short-circuiting. Keep the chain lazy and collect only at the end.

## Bad

```rust
// Three allocations, three passes
fn process_users(users: Vec<User>) -> Vec<String> {
    let active: Vec<_> = users.into_iter()
        .filter(|u| u.is_active)
        .collect();

    let verified: Vec<_> = active.into_iter()
        .filter(|u| u.is_verified)
        .collect();

    verified.into_iter()
        .map(|u| u.name)
        .collect()
}

// Collecting just to count, check, or sum
fn count_valid(items: &[Item]) -> usize {
    items.iter()
        .filter(|i| i.is_valid())
        .collect::<Vec<_>>()  // Unnecessary!
        .len()
}
```

## Good

```rust
struct User { is_active: bool, is_verified: bool, name: String }
struct Item { value: i64, valid: bool }
impl Item {
    fn is_valid(&self) -> bool { self.valid }
}

// One allocation, one pass
fn process_users(users: Vec<User>) -> Vec<String> {
    users.into_iter()
        .filter(|u| u.is_active)
        .filter(|u| u.is_verified)
        .map(|u| u.name)
        .collect()
}

// No allocation needed
fn count_valid(items: &[Item]) -> usize {
    items.iter().filter(|i| i.is_valid()).count()
}

// Short-circuits, no allocation
fn has_valid_items(items: &[Item]) -> bool {
    items.iter().any(|i| i.is_valid())
}

fn sum_valid(items: &[Item]) -> i64 {
    items.iter().filter(|i| i.is_valid()).map(|i| i.value).sum()
}
```

## Methods That Avoid Collecting

| Instead of collecting to... | Use |
|-----------------------------|-----|
| Check if empty / get first | `.next()` or `.next().is_some()` |
| Check if any / all match | `.any(pred)` / `.all(pred)` |
| Find first match | `.find(pred)` |
| Count elements | `.count()` |
| Sum elements | `.sum()` |
| Get last | `.last()` |

## Pattern: Deferred Collection

Return the iterator and let the caller decide.

```rust
struct RawData { ok: bool }
struct ProcessedData;
impl From<RawData> for ProcessedData {
    fn from(_: RawData) -> Self { ProcessedData }
}

fn prepare_data(raw: Vec<RawData>) -> impl Iterator<Item = ProcessedData> {
    raw.into_iter()
        .filter(|d| d.ok)
        .map(ProcessedData::from)
}
```

## When Intermediate Collection Is Needed

```rust
// Iterating more than once
let items: Vec<_> = data.iter()
    .filter(|x| x.is_valid())
    .collect();
let count = items.len();
for item in &items {
    process(item);
}

// Sorting or random access (needs a concrete collection)
let mut sorted: Vec<_> = data.iter()
    .filter(|x| x.is_active)
    .collect();
sorted.sort_by_key(|x| x.priority);
```

When you must collect, pre-allocate with `Vec::with_capacity` and `extend`.

## See Also

- [perf-iter-lazy](./perf-iter-lazy.md) - Keep iterators lazy
- [mem-with-capacity](./mem-with-capacity.md) - Pre-allocate collections
- [perf-iter-over-index](./perf-iter-over-index.md) - Iterator patterns
