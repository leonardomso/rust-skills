# own-move-large

> Borrow large values by default; box only when measured moves or type shape justify allocation

## Why It Matters

Rust move semantics transfer ownership, but they do not promise that the
machine will copy every byte: return-place optimization and ordinary compiler
optimization often elide physical moves. Boxing gives a stable-size handle at
the cost of allocation, indirection, allocator contention, and loss of
locality. Borrow when ownership need not move. Box for recursive types,
address-stability contracts, stack limits, or a measured hot move that
survives optimization—not from a universal size table.

## Bad

```rust
// Passing ownership when the function only needs mutation obscures the contract
struct GameState {
    board: [[Cell; 100]; 100],  // 10,000 cells
    history: [Move; 1000],       // 1,000 moves
    players: [Player; 4],        // Player data
    // Total: potentially tens of KB
}

fn process_state(state: GameState) -> GameState {
    let mut new_state = state;
    new_state.apply_rules();
    new_state
}

let state = GameState::new();
let state = process_state(state);
```

## Good

```rust
// Borrow when ownership never needs to change
struct GameState {
    board: [[Cell; 100]; 100],
    history: Vec<Move>,
    players: [Player; 4],
}

fn process_state(state: &mut GameState) {
    state.apply_rules();
}

let mut state = GameState::new();
process_state(&mut state);

// Box where recursive shape requires indirection
enum Node {
    Leaf(u64),
    Branch(Box<Node>, Box<Node>),
}
```

## When to Box

| Evidence | Recommendation |
|----------|----------------|
| Caller only reads or mutates in place | Borrow |
| Recursive type | Box one or more recursive edges |
| Address must not change after initialization | Pin an appropriate pointer and uphold pinning invariants |
| Stack exhaustion under representative depth/concurrency | Move selected storage to heap |
| Profile shows unavoidable large copies | Reshape or box the measured field |
| Size alone, no observed cost | Keep the simpler value layout |

## Stack vs Heap Tradeoffs

```rust
// Inline storage: contributes the full array to the enclosing value's size.
struct StackHeavy {
    data: [u8; 4096],
}

// Indirect storage: adds allocation and pointer indirection.
struct HeapLight {
    data: Box<[u8; 4096]>,
}

// Measure with size_of
use std::mem::size_of;
assert_eq!(size_of::<StackHeavy>(), 4096);
assert!(size_of::<HeapLight>() < size_of::<StackHeavy>());
```

## Alternative: References

When you don't need ownership transfer, use references:

```rust
// Borrowing expresses that ownership remains with the caller.
fn analyze_state(state: &GameState) -> Analysis {
    compute_analysis(state)
}

// Mutable borrow for in-place modification
fn update_state(state: &mut GameState) {
    state.tick();
}
```

## Do Not Box Every Builder Result

```rust
impl LargeConfig {
    pub fn builder() -> ConfigBuilder {
        ConfigBuilder::default()
    }
}

impl ConfigBuilder {
    pub fn build(self) -> LargeConfig {
        LargeConfig {
            // ... fields from builder
        }
    }
}
```

Let the caller choose `Box::new(builder.build())` when it needs heap ownership.
A constructor that always returns `Box<T>` hard-codes allocation into the API.

## Profile First

Don't prematurely optimize. Use tools to identify if moves are actually a bottleneck:

```rust
// Check type sizes
println!("Size of GameState: {}", std::mem::size_of::<GameState>());

// Profile with cargo flamegraph or perf to find hot memcpys
```

## See Also

- [own-copy-small](./own-copy-small.md) - Cheap types should be Copy
- [mem-box-large-variant](./mem-box-large-variant.md) - Boxing enum variants
- [perf-profile-first](./perf-profile-first.md) - Measure before optimizing
