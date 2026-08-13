# opt-cache-friendly

> Organize data for cache-efficient access patterns

## Why It Matters

Cache misses are expensive—a L3 cache miss costs ~100+ cycles vs ~4 cycles for L1 hit. Data layout and access patterns determine cache efficiency. Arrays of structs (AoS) vs structs of arrays (SoA), memory locality, and access patterns can make order-of-magnitude performance differences. Nested `Arc` / `Box` chains levy the same tax: each extra pointer is another miss before the hot field is in hand. Copy that field next to the loop unless a measurement says the hop is cheaper, or the value is large and several owners truly share it.

## Bad

```rust
use std::sync::Arc;

struct Theme {
    accent: u32,
}

struct Palette {
    theme: Arc<Theme>,
}

struct Stroke {
    palette: Arc<Palette>,
    pixels: Vec<u8>,
}

impl Stroke {
    fn accent(&self) -> u32 {
        self.palette.theme.accent
    }
}
```

## Good

```rust
use std::sync::Arc;

struct Theme {
    accent: u32,
}

struct Palette {
    theme: Arc<Theme>,
}

struct Stroke {
    palette: Arc<Palette>,
    pixels: Vec<u8>,
    accent: u32,
}

impl Stroke {
    fn accent(&self) -> u32 {
        self.accent
    }
}
```

Keep the shared `Palette` when it is large and genuinely has several owners.
Lift only a measured hot field, and update or reconstruct the copy whenever the
source configuration changes.

## Structure of Arrays

When a loop touches one field across thousands of records, splitting that hot
field into a contiguous vector can reduce unrelated cache traffic. It is not
automatically superior: an update that always reads a record's position and
velocity together may be better served by a compact array of structs. Benchmark
the actual access pattern.

## Hot/Cold Splitting

```rust
// Separate frequently and rarely accessed fields
struct EntityHot {
    position: [f32; 3],
    velocity: [f32; 3],
    // Hot data - accessed every frame
}

struct EntityCold {
    name: String,
    creation_time: Instant,
    metadata: HashMap<String, Value>,
    // Cold data - rarely accessed
}

struct Entities {
    hot: Vec<EntityHot>,
    cold: Vec<EntityCold>,
}

// Hot loop touches only hot data
fn update(entities: &mut Entities, dt: f32) {
    for e in &mut entities.hot {
        e.position[0] += e.velocity[0] * dt;
        // Cold data stays out of cache
    }
}
```

## Sequential Chunks

```rust
// Process in cache-line-sized chunks
const CACHE_LINE: usize = 64;

fn process_sequentially(data: &mut [u8]) {
    for chunk in data.chunks_mut(CACHE_LINE) {
        // Contiguous traversal exposes a predictable stream to hardware.
        process_chunk(chunk);
    }
}
```

## Avoid Pointer Chasing

```rust
// Bad: linked list - random memory access
struct Node {
    value: i32,
    next: Option<Box<Node>>,
}

fn sum_linked(head: &Node) -> i32 {
    // Each node is a cache miss
}

// Good: contiguous vector
fn sum_vector(data: &[i32]) -> i32 {
    data.iter().sum()  // Sequential access, prefetcher happy
}

// Good: if graph needed, use indices
struct Graph {
    values: Vec<i32>,
    edges: Vec<usize>,  // Indices into values
}
```

## Memory Layout Attributes

```rust
// Ensure cache-line alignment
#[repr(C, align(64))]
struct CacheAligned {
    data: [u8; 64],
}

// Prevent false sharing in concurrent code
#[repr(C, align(64))]
struct PaddedCounter {
    value: AtomicU64,
    _pad: [u8; 56],
}
```

## Measuring Cache Performance

```bash
# Linux perf
perf stat -e cache-references,cache-misses ./my_program

# Detailed cache analysis
perf stat -e L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses ./my_program

# Cachegrind
valgrind --tool=cachegrind ./my_program
```

## See Also

- [mem-smaller-integers](./mem-smaller-integers.md) - Smaller data fits more in cache
- [mem-box-large-variant](./mem-box-large-variant.md) - Keep enum sizes small
- [opt-bounds-check](./opt-bounds-check.md) - Sequential access patterns
- [own-arc-shared](./own-arc-shared.md) - One `Arc` for genuine sharing, not a pointer per nested field
- [perf-profile-first](./perf-profile-first.md) - Confirm pointer depth with a measurement
