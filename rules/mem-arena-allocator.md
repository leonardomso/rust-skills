# mem-arena-allocator

> Use arena allocators for batch allocations

## Why It Matters

Arena allocators (bump allocators) allocate memory from a contiguous region, making allocation extremely fast (just bump a pointer). All allocations are freed at once when the arena is dropped. Perfect for request-scoped or parse-tree allocations.

## Bad

```rust
// Many small allocations during parsing
fn parse(input: &str) -> Vec<Node> {
    let mut nodes = Vec::new();
    for token in tokenize(input) {
        nodes.push(Box::new(Node::new(token)));  // Heap alloc per node!
    }
    nodes
}

// Per-request allocations add up
fn handle_request(req: Request) -> Response {
    let headers = parse_headers(&req);      // Allocates
    let body = parse_body(&req);            // Allocates
    let response = generate_response();     // Allocates
    // All freed individually at end
    response
}
```

## Good

```rust
use bumpalo::Bump;

// All nodes allocated from same arena
fn parse<'a>(input: &str, arena: &'a Bump) -> Vec<&'a Node> {
    let mut nodes = Vec::new();
    for token in tokenize(input) {
        let node = arena.alloc(Node::new(token));  // Fast bump!
        nodes.push(node);
    }
    nodes
}  // Arena freed all at once

// Per-request arena
fn handle_request(req: Request) -> Response {
    let arena = Bump::new();
    
    let headers = parse_headers(&req, &arena);
    let body = parse_body(&req, &arena);
    let response = generate_response(&arena);
    
    // Convert to owned response before arena drops
    response.to_owned()
}  // All request memory freed instantly
```

## Thread-Local Scratch Arena Pattern

```rust
use bumpalo::Bump;
use std::cell::RefCell;

thread_local! {
    static SCRATCH: RefCell<Bump> = RefCell::new(Bump::with_capacity(4 * 1024));
}

/// Runs `f` with the scratch arena, then resets it. `T` cannot borrow from the
/// arena, because `f` must work for any arena lifetime.
fn with_scratch<T>(f: impl FnOnce(&Bump) -> T) -> T {
    SCRATCH.with(|scratch| {
        let mut arena = scratch.borrow_mut();
        let result = f(&arena);
        arena.reset(); // reuse the memory; never call this while `f` runs
        result
    })
}

// Usage
fn process_batch(items: &[Item]) -> Vec<Output> {
    with_scratch(|arena| {
        let temp_data: Vec<&TempData> = items
            .iter()
            .map(|item| &*arena.alloc(compute_temp(item)))
            .collect();

        // Use temp_data...
        finalize(&temp_data) // owned result; arena is reset after we return
    })
}
```

## Evidence from ROC Compiler

```rust
// https://github.com/roc-lang/roc/blob/main/crates/compiler/solve/src/to_var.rs
std::thread_local! {
    static SCRATCHPAD: RefCell<Option<bumpalo::Bump>> = 
        RefCell::new(Some(bumpalo::Bump::with_capacity(4 * 1024)));
}

fn take_scratchpad() -> bumpalo::Bump {
    SCRATCHPAD.with(|f| f.take().unwrap())
}

fn put_scratchpad(scratchpad: bumpalo::Bump) {
    SCRATCHPAD.with(|f| {
        f.replace(Some(scratchpad));
    });
}
```

## Bumpalo Collections

Enable the `collections` cargo feature (`bumpalo = { version = "3", features = ["collections"] }`). These are bumpalo's own `Vec` and `String` types, not `std::vec::Vec`.

```rust
use bumpalo::Bump;
use bumpalo::collections::{Vec, String};

fn process<'a>(arena: &'a Bump, input: &str) -> Vec<'a, String<'a>> {
    let mut results = Vec::new_in(arena);
    
    for word in input.split_whitespace() {
        let mut s = String::new_in(arena);
        s.push_str(word);
        s.push_str("_processed");
        results.push(s);
    }
    
    results  // All allocated in arena
}
```

## Standard Library Allocators

Since Rust 1.100 the standard `Allocator` trait and `Vec::new_in` / `Box::new_in` are stable, so you can write your own allocator without nightly. Whether a given arena crate implements std's trait is crate-specific. See [mem-allocator-api](mem-allocator-api.md).

## When to Use Arenas

| Situation | Use Arena? |
|-----------|-----------|
| Parsing (AST nodes) | Yes |
| Request handling | Yes |
| Batch processing | Yes |
| Long-lived data | No |
| Data escaping scope | No (or copy out) |
| Simple programs | Overkill |

## Performance Impact

Arena/bump allocation removes per-allocation metadata overhead and can be
substantially faster than the global allocator — often an order of magnitude in
microbenchmarks — but the actual speedup depends on the allocator, workload,
and allocation size. Arena reset is O(1) regardless of how many allocations
were made. Measure with [criterion](https://crates.io/crates/criterion) to
confirm the benefit in your specific use case.

```rust
// Memory trade-off:
// - Arena wastes some memory (unused capacity at the end)
// - But eliminates per-allocation metadata overhead
// - Frees everything in O(1) with a single bump reset
```

## See Also

- [mem-with-capacity](mem-with-capacity.md) - Pre-allocate when size is known
- [mem-reuse-collections](mem-reuse-collections.md) - Reuse collections with clear()
- [mem-allocator-api](mem-allocator-api.md) - Stable `Allocator` trait and `Vec::new_in`
- [perf-profile-first](perf-profile-first.md) - Profile to verify benefit
- [mem-global-allocator](mem-global-allocator.md) - Benchmark an alternative global allocator
