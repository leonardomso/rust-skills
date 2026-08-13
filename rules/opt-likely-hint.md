# opt-likely-hint

> Add branch-likelihood hints only from profiles and verify generated code

## Why It Matters

CPU branch prediction and compiler block layout can affect a measured hot path, but source ordering, an early `return`, or the first `match` arm is not a stable likelihood annotation. Optimizers use their own heuristics and profile information. A wrong hint can make code slower, and a right hint can become stale as traffic changes. Keep normal code structured for correctness/readability; add an explicit hint only after representative evidence identifies a material branch.

## Stable Rust

Rust 1.95 stabilized `std::hint::cold_path`, a hint that the execution path containing the call is unlikely:

```rust
fn decode(frame: &[u8]) -> Result<Message, DecodeError> {
    if frame.len() < HEADER_LEN {
        std::hint::cold_path();
        return Err(DecodeError::ShortFrame);
    }
    decode_valid_length(frame)
}
```

This is a compiler hint, not a semantic promise. It does not skip validation, make the branch impossible, guarantee a machine-code layout, or prevent speculation. Benchmark both versions and inspect optimized output on every supported architecture before retaining it.

A `#[cold]` helper is another stable hint when extracting a sizeable error path keeps the hot function clear:

```rust
fn decode(frame: &[u8]) -> Result<Message, DecodeError> {
    if frame.len() < HEADER_LEN {
        return short_frame();
    }
    decode_valid_length(frame)
}

#[cold]
fn short_frame<T>() -> Result<T, DecodeError> {
    Err(DecodeError::ShortFrame)
}
```

Do not add an allocation, backtrace, logging side effect, or changed error contract merely to create a cold helper.

## Nightly `likely` And `unlikely`

```rust
#![feature(likely_unlikely)]

fn process(data: &Data) -> Output {
    if std::hint::unlikely(data.is_corrupted()) {
        reject(data)
    } else {
        process_valid(data)
    }
}
```

`std::hint::likely` and `unlikely` remain unstable for the Rust 1.97 corpus. A stable production crate must not use them or silently require nightly. Do not add a third-party wrapper solely to imitate an unstable intrinsic without reviewing portability, implementation, maintenance, license, and benchmark evidence.

## What Does Not Convey Likelihood Reliably

```rust
fn classify(value: Option<u32>) -> u32 {
    match value {
        None => 0,
        Some(value) => value,
    }
}
```

The order of these arms and whether `None` uses an early return do not specify which case is likely. Structure the function for clear control flow and let measurement decide whether an explicit cold-path hint is warranted.

Similarly:

- listing a common enum variant first is not a branch probability contract;
- wrapping a predicate in `#[inline(always)]` does not create profile evidence;
- a microbenchmark with one fixed distribution does not represent production tenants;
- a lower branch-miss count can still regress latency through code-size or cache effects.

## PGO First For Broad Decisions

When branch behavior is stable and widespread, profile-guided optimization can inform many layout decisions from a versioned representative workload. It still requires holdout validation and source/workload/toolchain provenance. Hand-written hints are best reserved for a small stable invariant such as a genuinely exceptional error path whose distribution is continuously observed.

## Verification Contract

1. Record branch frequencies and product impact on representative traffic without logging sensitive inputs.
2. Benchmark baseline and candidate with controlled inputs and uncertainty.
3. Inspect optimized assembly/IR for the supported targets to confirm the hint changed the intended path.
4. Check binary size, instruction-cache behavior, throughput, and tail latency—not only branch misses.
5. Re-run after compiler, target CPU, PGO data, or workload-distribution changes.
6. Remove the hint when evidence disappears; do not preserve it as folklore.

## See Also

- [opt-cold-unlikely](./opt-cold-unlikely.md) - isolate measured cold functions
- [opt-inline-never-cold](./opt-inline-never-cold.md) - use codegen hints sparingly
- [opt-pgo-profile](opt-pgo-profile.md) - train and validate profile-guided optimization
- [perf-profile-first](./perf-profile-first.md) - define evidence before tuning
