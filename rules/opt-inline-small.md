# opt-inline-small

> Add `#[inline]` only at measured optimization boundaries

## Why It Matters

Inlining can remove a call boundary and expose constant propagation or vectorization, but it can also duplicate code, increase compile time, and hurt instruction-cache locality. Rust does not guarantee that `#[inline]` or `#[inline(always)]` produces an inlined machine-code body. Same-crate and generic functions are already optimization candidates. Treat the attribute as a code-generation hint retained by benchmark and optimized-output evidence.

## Bad

```rust
#[inline]
pub fn len(&self) -> usize {
    self.inner.len()
}
```

Small source size and public visibility alone do not show this method is hot or that a retained call exists. Adding hints to every accessor grows metadata and constrains future tuning without demonstrated value.

## Good

```rust
// A representative cross-crate benchmark showed a retained call here blocked
// vectorization on supported targets; generated-code CI records the boundary.
#[inline]
pub fn decode_lane(value: u32, mask: u32) -> u32 {
    (value & mask).rotate_left(3)
}
```

The comment describes the evidence, not a promised speedup. If the compiler later optimizes the baseline equally, remove the annotation.

## Attribute Semantics

```rust
fn compiler_decides() {}

#[inline]
fn request_inline_consideration() {}

#[inline(always)]
fn make_a_stronger_request() {}

#[inline(never)]
fn request_a_call_boundary() {}
```

All are hints to code generation rather than semantic guarantees. Recursion, target constraints, optimization level, LTO, compiler heuristics, and code shape can change the result. `#[inline(never)]` is likewise a strong request, not an absolute promise.

## Cross-Crate Boundaries

Without whole-program LTO, an ordinary non-generic function body may be unavailable for downstream inlining. `#[inline]` can make a body available in crate metadata. That is a reason to test a candidate, not to annotate every public function. Generic/opaque code often already needs downstream monomorphization; inspect the actual artifact before claiming the attribute is required.

An `#[inline]` outer function does not automatically make every private callee body available downstream. Annotate only the exact measured boundary or refactor a genuinely tiny helper into the exposed body when that remains maintainable.

## Cold Paths

Use `#[cold]` and/or `#[inline(never)]` only when a profile shows sizeable rare code contaminating a hot path. Do not introduce process exits, logging, backtraces, or changed error construction merely to force a boundary. Verify error semantics and optimized layout separately.

## Verification

```bash
cargo rustc --locked --profile release-service -- --emit=asm
```

Use pinned inspection tools where practical and compare baseline/candidate assembly, object size, clean build time, throughput, and tail latency on supported targets. A missing `call` instruction alone is not sufficient: code duplication and cache behavior may dominate. Re-run after compiler, profile, LTO, target CPU, or workload changes.

## Decision Guide

| Evidence | Action |
|---|---|
| No measured hot boundary | Let the compiler decide |
| Cross-crate call blocks a demonstrated optimization | Try `#[inline]`, benchmark, inspect |
| Tiny critical helper still not inlined and candidate wins | Consider `#[inline(always)]` with stronger code-size review |
| Rare sizeable error construction affects hot layout | Consider `#[cold]`/`#[inline(never)]` |
| Annotation no longer changes product metrics | Remove it |

## See Also

- [opt-inline-always-rare](opt-inline-always-rare.md) - review stronger inline requests
- [opt-inline-never-cold](opt-inline-never-cold.md) - isolate measured cold code
- [opt-lto-release](opt-lto-release.md) - benchmark whole-artifact LTO
- [perf-profile-first](perf-profile-first.md) - retain only evidence-backed tuning
