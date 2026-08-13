# perf-ahash

> Change hashers only after profiling and an explicit key-threat analysis

## Why It Matters

The standard `HashMap` default is randomized and designed to resist common
hash-flooding attacks; its exact algorithm is not a stable API promise. A
different hasher may improve a measured, map-heavy workload with trusted keys,
but it changes collision behavior, dependency surface, portability, and attack
resistance. Never select one from a generic speed ratio. Keep the default for
untrusted keys unless a security review of the concrete hasher and deployment
threat model approves otherwise.

## Bad

```rust
use std::collections::HashMap;

// This map is not known to be hot; changing its hasher speculatively adds a
// dependency and a security decision without evidence.
fn build_id_map(ids: &[(u32, String)]) -> HashMap<u32, String> {
    ids.iter().cloned().collect()
}
```

## Good

```rust
// AHashMap is one candidate after measurement and threat-model review.
use ahash::AHashMap;

fn build_id_map_ahash(ids: &[(u32, String)]) -> AHashMap<u32, String> {
    ids.iter().cloned().collect()
}

// FxHashMap (rustc-hash): a predictable candidate for trusted keys.
// Only for trusted integer or pointer keys where hash flooding is not a concern
// (e.g., compiler internals, in-process caches keyed by integer IDs).
use rustc_hash::FxHashMap;

type NodeMap<V> = FxHashMap<u32, V>;

fn build_node_map(nodes: &[(u32, String)]) -> NodeMap<String> {
    let mut map = NodeMap::with_capacity_and_hasher(
        nodes.len(),
        Default::default(),
    );
    map.extend(nodes.iter().cloned());
    map
}

// Convenient type aliases to avoid repeating the hasher parameter
use std::collections::HashMap;
use rustc_hash::FxBuildHasher;

type FastMap<K, V> = HashMap<K, V, FxBuildHasher>;

fn fast_map_example() -> FastMap<u32, u64> {
    FastMap::with_capacity_and_hasher(64, FxBuildHasher)
}
```

## Hasher Selection Guide

| Hasher | Collision/key posture | Use when |
|--------|-----------------------|----------|
| std default | Randomized, general-purpose default | Untrusted or mixed keys; no measured reason to change |
| `ahash` | Randomized but not a cryptographic primitive | Reviewed deployment and measured workload justify it |
| `FxHash` | Predictable | Trusted keys in a closed process only |

## Key Points

- **Profile first**: switch hashers only after confirming map operations appear in profiler output.
- `ahash::AHashMap` has a similar map API, but changing the public concrete type
  or serialized/debug order can still affect callers.
- `FxHashMap` is what rustc uses internally; it is predictable, so never expose it to externally-supplied keys.
- Pass `with_capacity` when the final size is known — it applies regardless of hasher choice.

## See Also

- [perf-entry-api](perf-entry-api.md) - avoid redundant lookups with the entry API
- [perf-profile-first](perf-profile-first.md) - profile before optimizing
- [mem-with-capacity](mem-with-capacity.md) - pre-allocate collections when size is known
