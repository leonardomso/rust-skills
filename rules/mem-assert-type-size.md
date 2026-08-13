# mem-assert-type-size

> Add target-scoped size budgets only for measured, high-cardinality types

## Why It Matters

A field or enum-layout change can increase memory and cache pressure when millions of values are live. `size_of::<T>()` is compiler- and target-specific for ordinary Rust types; an assertion detects drift in one compiled configuration but does not create a stable ABI or wire layout. Add a budget only after measuring live cardinality and showing that object size materially affects the product objective.

## Bad

```rust
struct Event {
    timestamp: u64,
    kind: EventKind,
    payload: [u8; 32],
}

// False portability promise: the expected value was copied from one target.
const _: () = assert!(std::mem::size_of::<Event>() == 48);
```

The result depends on `EventKind`, target pointer width/alignment, compiler layout decisions, features, and toolchain. An exact assertion also rejects harmless shrinkage.

## Good

```rust
#[derive(Clone, Copy)]
enum EventKind {
    Created,
    Updated,
}

struct Event {
    timestamp: u64,
    kind: EventKind,
    payload: [u8; 32],
}

// This budget is evidence for the admitted 64-bit targets, not an ABI promise.
#[cfg(target_pointer_width = "64")]
const _: () = assert!(
    std::mem::size_of::<Event>() <= 48,
    "Event exceeded its measured 64-bit resident-size budget",
);
```

Use a maximum unless exact size is the actual reviewed contract. Keep target-specific expectations separate and exercise every supported target in CI.

## Regression Test With Context

```rust
#[cfg(all(test, target_pointer_width = "64"))]
mod size_budget {
    use super::Event;

    #[test]
    fn event_stays_within_resident_memory_budget() {
        const LIVE_EVENTS: usize = 2_000_000;
        const MAX_TOTAL_BYTES: usize = 96 * 1024 * 1024;
        let element = std::mem::size_of::<Event>();
        let total = element
            .checked_mul(LIVE_EVENTS)
            .expect("size model fits usize on supported 64-bit targets");
        assert!(total <= MAX_TOTAL_BYTES, "{element} bytes per Event");
    }
}
```

This is still a model: `Vec` capacity, allocator metadata, fragmentation, referenced allocations, and surrounding indexes add memory. Confirm the live process with representative load and a memory profiler.

## Layout Contracts Are Different

```rust
#[repr(C)]
pub struct NativeHeader {
    pub version: u16,
    pub flags: u16,
    pub length: u32,
}

#[cfg(all(target_endian = "little", target_pointer_width = "64"))]
const _: () = {
    assert!(std::mem::size_of::<NativeHeader>() == 8);
    assert!(std::mem::align_of::<NativeHeader>() == 4);
};
```

`repr(C)` gives a C-compatible field-layout algorithm for one target; it does not define byte order, C compiler options, padding contents, pointer validity, or a portable wire/storage format. For FFI, validate size, alignment, offsets, enum/discriminant representation, target ABI, and the matching C header in a cross-language test. For network or durable storage, serialize logical fields explicitly and version the schema instead of copying raw struct bytes.

## Rust Layout

- A passing assertion on a default-representation struct or enum does not make its layout stable across compiler releases.
- `repr(transparent)` and `repr(C)` should appear only when their representation is an intentional external contract, not to force a performance budget.
- Niche optimization, field reordering, pointer width, alignment, and feature-selected fields can change size.
- `size_of` excludes heap allocations owned through `String`, `Vec`, `Box`, `Arc`, and similar handles.
- Cache-line claims require target-aware measurement; “at most 64 bytes” does not guarantee placement in one cache line or prevent false sharing.

## Admission And Failure Behavior

1. Record the benchmark/profile that justified the budget and the supported targets it covers.
2. Fail the target-specific gate when the budget grows; review impact rather than blindly raising the constant.
3. Accept a new size only with updated resident-memory/cache evidence and rollout observability.
4. Re-run after toolchain, target, feature, allocator, or representation changes.
5. Remove the assertion when cardinality or architecture changes make it tautological or irrelevant.

## See Also

- [mem-box-large-variant](./mem-box-large-variant.md) - reduce a measured enum-size bottleneck
- [opt-cache-friendly](./opt-cache-friendly.md) - measure locality and false sharing
- [async-future-size](./async-future-size.md) - target-scoped future-size budgets
- [type-repr-transparent](type-repr-transparent.md) - use representation attributes only for external contracts
