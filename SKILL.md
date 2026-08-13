---
name: rust-skills
description: >
  Comprehensive Rust coding guidelines with 343 rules across 27 categories.
  Use when writing, reviewing, or refactoring Rust code. Covers ownership,
  error handling, async patterns, concurrency, unsafe code, API design, memory
  optimization, performance, numeric safety, conversions, serde, pattern
  matching, macros, closures, observability, testing, FFI, and common
  anti-patterns.
  Invoke with /rust-skills.
license: MIT
metadata:
  author: leonardomso
  version: "1.5.1"
  sources:
    - Rust API Guidelines
    - Rust Performance Book
    - Rust 2024 Edition Guide
    - The Rustonomicon
    - ripgrep, tokio, serde, polars, axum, cargo codebases
    - Microsoft Pragmatic Rust Guidelines
    - Zero To Production In Rust
---

# Rust Best Practices

Comprehensive guide for writing correct, maintainable, production-grade Rust.
Contains 343 rules across 27 categories, prioritized by impact for use by
humans and LLMs in code generation and review. Current for Rust 1.97.1
(2024 edition).

## When to Apply

Reference these guidelines when:
- Writing new Rust functions, structs, or modules
- Implementing error handling or async code
- Writing concurrent, parallel, or `unsafe` code
- Writing FFI shims or `-sys` / `-ffi` crates
- Designing public APIs for libraries
- Reviewing code for ownership/borrowing issues
- Optimizing memory usage or reducing allocations
- Tuning performance for hot paths
- Refactoring existing Rust code

## Rule Categories by Priority

| Priority | Category | Impact | Prefix | Rules |
|----------|----------|--------|--------|-------|
| 1 | Ownership & Borrowing | CRITICAL | `own-` | 12 |
| 2 | Error Handling | CRITICAL | `err-` | 16 |
| 3 | Memory Optimization | CRITICAL | `mem-` | 18 |
| 4 | Unsafe Code | CRITICAL | `unsafe-` | 10 |
| 5 | API Design | HIGH | `api-` | 35 |
| 6 | Async/Await | HIGH | `async-` | 24 |
| 7 | Concurrency | HIGH | `conc-` | 6 |
| 8 | Compiler Optimization | HIGH | `opt-` | 12 |
| 9 | Numeric & Arithmetic Safety | HIGH | `num-` | 6 |
| 10 | Type Safety | MEDIUM | `type-` | 14 |
| 11 | Trait & Generics Design | MEDIUM | `trait-` | 7 |
| 12 | Conversions | MEDIUM | `conv-` | 3 |
| 13 | Const & Compile-Time | MEDIUM | `const-` | 5 |
| 14 | Serde | MEDIUM | `serde-` | 8 |
| 15 | Pattern Matching | MEDIUM | `pat-` | 6 |
| 16 | Macros | MEDIUM | `macro-` | 11 |
| 17 | Closures | MEDIUM | `closure-` | 5 |
| 18 | Collections | MEDIUM | `coll-` | 4 |
| 19 | Naming Conventions | MEDIUM | `name-` | 18 |
| 20 | Testing | MEDIUM | `test-` | 19 |
| 21 | Documentation | MEDIUM | `doc-` | 16 |
| 22 | Observability | MEDIUM | `obs-` | 9 |
| 23 | Performance Patterns | MEDIUM | `perf-` | 15 |
| 24 | Project Structure | LOW | `proj-` | 27 |
| 25 | FFI & Interop | LOW | `ffi-` | 5 |
| 26 | Clippy & Linting | LOW | `lint-` | 16 |
| 27 | Anti-patterns | REFERENCE | `anti-` | 16 |

---

## Quick Reference

### 1. Ownership & Borrowing (CRITICAL)

- [`own-borrow-over-clone`](rules/own-borrow-over-clone.md) - Prefer `&T` borrowing over `.clone()`
- [`own-slice-over-vec`](rules/own-slice-over-vec.md) - Accept `&[T]` not `&Vec<T>`, `&str` not `&String`
- [`own-cow-conditional`](rules/own-cow-conditional.md) - Use `Cow<'a, T>` for conditional ownership
- [`own-arc-shared`](rules/own-arc-shared.md) - Use `Arc<T>` for shared ownership that must cross thread boundaries
- [`own-rc-single-thread`](rules/own-rc-single-thread.md) - Use `Rc<T>` for shared ownership in single-threaded contexts
- [`own-refcell-interior`](rules/own-refcell-interior.md) - Use `RefCell<T>` only for deliberate single-threaded interior mutability
- [`own-mutex-interior`](rules/own-mutex-interior.md) - Use `Mutex<T>` for interior mutability across threads
- [`own-rwlock-readers`](rules/own-rwlock-readers.md) - Benchmark `RwLock<T>` for read-heavy shared state; do not assume readers make it faster
- [`own-copy-small`](rules/own-copy-small.md) - Implement `Copy` when implicit duplication matches the type's semantics
- [`own-clone-explicit`](rules/own-clone-explicit.md) - Use explicit `Clone` for types where copying has meaningful cost
- [`own-move-large`](rules/own-move-large.md) - Borrow large values by default; box only when measured moves or type shape justify allocation
- [`own-lifetime-elision`](rules/own-lifetime-elision.md) - Rely on lifetime elision rules; add explicit lifetimes only when required

### 2. Error Handling (CRITICAL)

- [`err-thiserror-lib`](rules/err-thiserror-lib.md) - Use `thiserror` for library error types
- [`err-anyhow-app`](rules/err-anyhow-app.md) - Use `anyhow` for application error handling
- [`err-result-over-panic`](rules/err-result-over-panic.md) - Return `Result<T, E>` instead of panicking for recoverable errors
- [`err-context-chain`](rules/err-context-chain.md) - Add context with `.context()` or `.with_context()`
- [`err-no-unwrap-prod`](rules/err-no-unwrap-prod.md) - Avoid `unwrap()` in production code; use `?`, `expect()`, or handle errors
- [`err-expect-bugs-only`](rules/err-expect-bugs-only.md) - Use `expect()` only for invariants that indicate bugs, not user errors
- [`err-question-mark`](rules/err-question-mark.md) - Use `?` operator for clean propagation
- [`err-from-impl`](rules/err-from-impl.md) - Implement `From<E>` for error conversions to enable `?` operator
- [`err-source-chain`](rules/err-source-chain.md) - Preserve error chains with `#[source]` or `source()` method
- [`err-lowercase-msg`](rules/err-lowercase-msg.md) - Start error messages lowercase, no trailing punctuation
- [`err-doc-errors`](rules/err-doc-errors.md) - Document error conditions with `# Errors` section in doc comments
- [`err-custom-type`](rules/err-custom-type.md) - Define custom error types for domain-specific failures
- [`err-catch-unwind-boundary`](rules/err-catch-unwind-boundary.md) - Use `catch_unwind` only at a task, FFI, or process isolation edge, and pair it with a restart policy
- [`err-canonical-struct`](rules/err-canonical-struct.md) - Keep extensible library errors opaque, preserve `source()`, and expose only stable recovery queries
- [`err-panic-message`](rules/err-panic-message.md) - Give every intentional production panic a message that identifies the violated contract and relevant values
- [`err-edge-mapping`](rules/err-edge-mapping.md) - Keep domain and infrastructure errors protocol-neutral; map them to safe, actionable responses at the entrypoint

### 3. Memory Optimization (CRITICAL)

- [`mem-with-capacity`](rules/mem-with-capacity.md) - Use `with_capacity()` when size is known
- [`mem-smallvec`](rules/mem-smallvec.md) - Use `SmallVec` for usually-small collections
- [`mem-arrayvec`](rules/mem-arrayvec.md) - Use `ArrayVec<T, N>` when the collection itself needs fixed inline capacity
- [`mem-box-large-variant`](rules/mem-box-large-variant.md) - Box large enum variants to reduce overall enum size
- [`mem-boxed-slice`](rules/mem-boxed-slice.md) - Use `Box<[T]>`, `Arc<[T]>`, or `Arc<str>` for internal fixed-size heap data
- [`mem-thinvec`](rules/mem-thinvec.md) - Consider `ThinVec<T>` only after measuring many sparse collection handles
- [`mem-clone-from`](rules/mem-clone-from.md) - Use `clone_from()` to reuse allocations when repeatedly cloning
- [`mem-reuse-collections`](rules/mem-reuse-collections.md) - Clear and reuse collections instead of creating new ones in loops
- [`mem-avoid-format`](rules/mem-avoid-format.md) - Avoid `format!()` when string literals work
- [`mem-write-over-format`](rules/mem-write-over-format.md) - Use `write!()` into existing buffers instead of `format!()` allocations
- [`mem-arena-allocator`](rules/mem-arena-allocator.md) - Use arena allocators for batch allocations
- [`mem-zero-copy`](rules/mem-zero-copy.md) - Use zero-copy patterns with slices and `Bytes`
- [`mem-compact-string`](rules/mem-compact-string.md) - Use compact string types for memory-constrained string storage
- [`mem-smaller-integers`](rules/mem-smaller-integers.md) - Use appropriately-sized integers to reduce memory footprint
- [`mem-assert-type-size`](rules/mem-assert-type-size.md) - Add target-scoped size budgets only for measured, high-cardinality types
- [`mem-take-replace`](rules/mem-take-replace.md) - Use `mem::take` / `mem::replace` to move a value out of a `&mut` without cloning
- [`mem-drop-order`](rules/mem-drop-order.md) - Know and control drop order: struct fields drop top-to-bottom, locals in reverse
- [`mem-shrink-to-fit`](rules/mem-shrink-to-fit.md) - Reclaim measured, long-lived collection slack after growth has finished; do not assume an exact capacity

### 4. Unsafe Code (CRITICAL)

- [`unsafe-safety-comment`](rules/unsafe-safety-comment.md) - Write a `// SAFETY:` comment above every `unsafe` block and a `# Safety` section in every `unsafe fn`.
- [`unsafe-minimize-scope`](rules/unsafe-minimize-scope.md) - Keep each unsafe block limited to operations covered by one local proof
- [`unsafe-miri-ci`](rules/unsafe-miri-ci.md) - Run `cargo miri test` in CI for every crate that contains `unsafe` code.
- [`unsafe-maybeuninit`](rules/unsafe-maybeuninit.md) - Use `MaybeUninit<T>` for uninitialized memory; never use `mem::uninitialized()` or `mem::zeroed()` for types with validity invariants.
- [`unsafe-extern-block`](rules/unsafe-extern-block.md) - In Rust 2024, wrap `extern` blocks in `unsafe extern { }` and annotate each item as `safe` or `unsafe`.
- [`unsafe-send-sync-manual`](rules/unsafe-send-sync-manual.md) - Manually implement `Send` or `Sync` only with a complete ownership and concurrency proof
- [`unsafe-no-mangle-unsafe`](rules/unsafe-no-mangle-unsafe.md) - In Rust 2024, write `#[unsafe(no_mangle)]`, `#[unsafe(export_name = "...")]`, and `#[unsafe(link_section = "...")]` — not the bare attribute forms.
- [`unsafe-means-ub`](rules/unsafe-means-ub.md) - Mark a function or trait `unsafe` only when misuse can cause undefined behavior, not because it is merely dangerous
- [`unsafe-justify-use`](rules/unsafe-justify-use.md) - Use `unsafe` only for a novel abstraction, a measured hot path, or FFI / platform code — never as an ad-hoc shortcut
- [`unsafe-sound-abstractions`](rules/unsafe-sound-abstractions.md) - Never expose a safe API that can hit undefined behavior; if the caller must uphold a UB precondition, the function is `unsafe`

### 5. API Design (HIGH)

- [`api-builder-pattern`](rules/api-builder-pattern.md) - Use Builder pattern for complex construction
- [`api-builder-must-use`](rules/api-builder-must-use.md) - Mark builder methods with `#[must_use]` to prevent silent drops
- [`api-newtype-safety`](rules/api-newtype-safety.md) - Use newtypes to prevent mixing semantically different values
- [`api-typestate`](rules/api-typestate.md) - Use typestate pattern to encode state machine invariants in the type system
- [`api-sealed-trait`](rules/api-sealed-trait.md) - Use sealed traits to prevent external implementations while allowing use
- [`api-extension-trait`](rules/api-extension-trait.md) - Use extension traits to add methods to external types
- [`api-parse-dont-validate`](rules/api-parse-dont-validate.md) - Convert boundary data into types that preserve local invariants
- [`api-impl-into`](rules/api-impl-into.md) - Accept `impl Into<T>` for flexible APIs, implement `From<T>` for conversions
- [`api-impl-asref`](rules/api-impl-asref.md) - Use `AsRef<T>` when you only need to borrow the inner data
- [`api-must-use`](rules/api-must-use.md) - Mark types and functions with `#[must_use]` when ignoring results is likely a bug
- [`api-non-exhaustive`](rules/api-non-exhaustive.md) - Use `#[non_exhaustive]` on public enums and structs for forward compatibility
- [`api-from-not-into`](rules/api-from-not-into.md) - Implement `From<T>`, not `Into<U>` - From gives you Into for free
- [`api-default-impl`](rules/api-default-impl.md) - Implement `Default` for types with sensible default values
- [`api-common-traits`](rules/api-common-traits.md) - Implement standard traits (Debug, Clone, PartialEq, etc.) for public types
- [`api-serde-optional`](rules/api-serde-optional.md) - Make serde a feature flag, not a hard dependency for library crates
- [`api-impl-fromiterator`](rules/api-impl-fromiterator.md) - Implement `FromIterator` and `Extend` for collection types, and `IntoIterator` for all three reference forms
- [`api-operator-overload`](rules/api-operator-overload.md) - Overload operators only when the semantics are natural and unsurprising
- [`api-impl-io`](rules/api-impl-io.md) - Accept `impl Read` / `impl Write` (or the async equivalents) instead of a concrete file or socket
- [`api-inherent-core`](rules/api-inherent-core.md) - Put a type's essential methods on the type itself; implement traits by forwarding to them
- [`api-no-wrapper-params`](rules/api-no-wrapper-params.md) - Keep `Rc`, `Arc`, `Box`, and `RefCell` out of public function signatures unless sharing is the API
- [`api-param-order`](rules/api-param-order.md) - Keep the same conceptual parameters in the same order across related functions
- [`api-impl-rangebounds`](rules/api-impl-rangebounds.md) - Accept `impl RangeBounds<T>` for range parameters instead of a pair of endpoints or a concrete `Range`
- [`api-service-clone`](rules/api-service-clone.md) - Expose long-lived services as cheap `Clone` handles around `Arc<Inner>`, not as fat values callers must wrap themselves
- [`api-std-types-boundary`](rules/api-std-types-boundary.md) - Keep third-party types out of the public surface unless that crate is an intentional part of the contract
- [`api-free-functions`](rules/api-free-functions.md) - Put construction on the type; put computation with no receiver at module scope
- [`api-init-cascaded`](rules/api-init-cascaded.md) - Group four or more required constructor parameters into semantic helper types
- [`api-extract-or-reject`](rules/api-extract-or-reject.md) - Parse and validate transport input before handler logic; reject malformed requests without side effects
- [`api-health-probes`](rules/api-health-probes.md) - Separate liveness from readiness, keep probes cheap, and never perform business side effects
- [`api-password-auth`](rules/api-password-auth.md) - Hash passwords with a maintained memory-hard scheme and make authentication failures indistinguishable
- [`api-session-security`](rules/api-session-security.md) - Use opaque server-side sessions, rotate identifiers on privilege change, and enforce secure cookie policy
- [`api-idempotency-key`](rules/api-idempotency-key.md) - Scope idempotency keys to the caller, serialize concurrent duplicates, and replay the original outcome
- [`api-authz-fail-closed`](rules/api-authz-fail-closed.md) - Authenticate the principal, authorize the operation, and deny access unless both decisions succeed
- [`api-browser-security`](rules/api-browser-security.md) - Escape untrusted output, protect state-changing browser requests from CSRF, and authenticate redirect state
- [`api-password-reset`](rules/api-password-reset.md) - Make password change and recovery single-use, time-bounded, rate-limited security workflows
- [`api-tls-required`](rules/api-tls-required.md) - Require authenticated TLS for production network hops and never silently downgrade certificate validation

### 6. Async/Await (HIGH)

- [`async-tokio-runtime`](rules/async-tokio-runtime.md) - Own one observable Tokio runtime and isolate blocking or CPU work behind bounded admission
- [`async-no-lock-await`](rules/async-no-lock-await.md) - Never hold a synchronous lock across `.await`; make async lock scope an explicit ownership contract
- [`async-spawn-blocking`](rules/async-spawn-blocking.md) - Move blocking calls off executor threads and bound sustained CPU work
- [`async-tokio-fs`](rules/async-tokio-fs.md) - Isolate filesystem blocking and bound file work, bytes, and concurrency
- [`async-cancellation-token`](rules/async-cancellation-token.md) - Use `CancellationToken` for graceful shutdown and task cancellation
- [`async-join-parallel`](rules/async-join-parallel.md) - Join a small fixed set of independent, cancellation-safe futures
- [`async-try-join`](rules/async-try-join.md) - Use `try_join!` only when unfinished branches are safe to drop on error
- [`async-select-racing`](rules/async-select-racing.md) - Use `select!` to race futures and handle the first to complete
- [`async-bounded-channel`](rules/async-bounded-channel.md) - Use bounded channels to apply backpressure and prevent unbounded memory growth
- [`async-mpsc-queue`](rules/async-mpsc-queue.md) - Use `mpsc` channels for async message queues between tasks
- [`async-broadcast-pubsub`](rules/async-broadcast-pubsub.md) - Use `broadcast` channel for pub/sub where all subscribers receive all messages
- [`async-watch-latest`](rules/async-watch-latest.md) - Use `watch` channel for sharing the latest value with multiple observers
- [`async-oneshot-response`](rules/async-oneshot-response.md) - Use `oneshot` channel for request-response patterns
- [`async-joinset-structured`](rules/async-joinset-structured.md) - Use `JoinSet` for managing dynamic collections of spawned tasks
- [`async-clone-before-await`](rules/async-clone-before-await.md) - Clone shared ownership for spawned work; do not clone merely because code awaits
- [`async-fn-in-trait`](rules/async-fn-in-trait.md) - Use native async trait methods for static dispatch; box futures deliberately for `dyn`
- [`async-async-fn-bounds`](rules/async-async-fn-bounds.md) - Use `AsyncFn`/`AsyncFnMut`/`AsyncFnOnce` bounds instead of `F: Fn() -> Fut, Fut: Future`
- [`async-cancel-safety`](rules/async-cancel-safety.md) - Ensure futures used in `tokio::select!` branches are cancellation-safe
- [`async-yield-cpu`](rules/async-yield-cpu.md) - Bound CPU work on executor threads; consume cooperative budget or move sustained work to a compute pool
- [`async-assert-send`](rules/async-assert-send.md) - Assert that public futures and handles are `Send` so they can move across Tokio workers
- [`async-future-size`](rules/async-future-size.md) - Keep frequently created futures small by dropping large setup state before the first suspension point
- [`async-fn-over-future`](rules/async-fn-over-future.md) - Prefer `async fn` for readability; return `impl Future` when bounds or capture are the contract
- [`async-http-client-reuse`](rules/async-http-client-reuse.md) - Reuse one configured HTTP client per service and require deadlines on every outbound call
- [`async-durable-worker`](rules/async-durable-worker.md) - Claim durable work atomically, bound retries with backoff and jitter, and make worker shutdown explicit

### 7. Concurrency (HIGH)

- [`conc-rayon-par-iter`](rules/conc-rayon-par-iter.md) - Use rayon's `par_iter()` for CPU-bound data parallelism
- [`conc-scoped-threads`](rules/conc-scoped-threads.md) - Use `std::thread::scope` to borrow stack data across threads
- [`conc-atomic-ordering`](rules/conc-atomic-ordering.md) - Use the weakest correct memory `Ordering` for every atomic operation
- [`conc-thread-local`](rules/conc-thread-local.md) - Prefer `thread_local!` with `Cell`/`RefCell` over `static mut`
- [`conc-db-transaction-boundary`](rules/conc-db-transaction-boundary.md) - Keep one atomic business change inside one short database transaction
- [`conc-atomic-update`](rules/conc-atomic-update.md) - Use atomic `update` / `try_update` instead of hand-written compare-exchange loops

### 8. Compiler Optimization (HIGH)

- [`opt-inline-small`](rules/opt-inline-small.md) - Add `#[inline]` only at measured optimization boundaries
- [`opt-inline-always-rare`](rules/opt-inline-always-rare.md) - Use `#[inline(always)]` sparingly—only for critical hot paths proven by profiling
- [`opt-inline-never-cold`](rules/opt-inline-never-cold.md) - Use `#[inline(never)]` and `#[cold]` for error paths and rarely-executed code
- [`opt-cold-unlikely`](rules/opt-cold-unlikely.md) - Mark unlikely code paths with `#[cold]` to help compiler optimization
- [`opt-likely-hint`](rules/opt-likely-hint.md) - Add branch-likelihood hints only from profiles and verify generated code
- [`opt-lto-release`](rules/opt-lto-release.md) - Benchmark LTO modes on final binaries; do not assume fat LTO wins
- [`opt-codegen-units`](rules/opt-codegen-units.md) - Measure codegen-unit count as a build-throughput and runtime trade-off
- [`opt-pgo-profile`](rules/opt-pgo-profile.md) - Adopt PGO only with representative profiles, pinned tools, and measured wins
- [`opt-target-cpu`](rules/opt-target-cpu.md) - Compile server applications for the highest CPU baseline guaranteed across the deployment fleet
- [`opt-bounds-check`](rules/opt-bounds-check.md) - Prefer safe traversal that exposes bounds; verify optimized hot loops before considering unchecked access
- [`opt-simd-portable`](rules/opt-simd-portable.md) - Use portable SIMD for vectorized operations across architectures
- [`opt-cache-friendly`](rules/opt-cache-friendly.md) - Organize data for cache-efficient access patterns

### 9. Numeric & Arithmetic Safety (HIGH)

- [`num-overflow-explicit`](rules/num-overflow-explicit.md) - Handle integer overflow explicitly: `checked_`/`saturating_`/`wrapping_`/`overflowing_`
- [`num-cast-try-from`](rules/num-cast-try-from.md) - Avoid `as` for narrowing casts; use `From` for widening and `TryFrom` for narrowing
- [`num-float-compare`](rules/num-float-compare.md) - Don't compare floats with `==`; use a tolerance, and `total_cmp` for ordering
- [`num-saturating-clamp`](rules/num-saturating-clamp.md) - Bound values with `clamp` and saturating arithmetic
- [`num-nonzero`](rules/num-nonzero.md) - Use `NonZero*` types to forbid zero and unlock the niche optimization
- [`num-bit-width`](rules/num-bit-width.md) - Use integer `bit_width` / `highest_one` / `isolate_*_one` instead of hand-rolled bit math

### 10. Type Safety (MEDIUM)

- [`type-newtype-ids`](rules/type-newtype-ids.md) - Wrap IDs in newtypes: `UserId(u64)`
- [`type-newtype-validated`](rules/type-newtype-validated.md) - Use newtypes to enforce validation at construction time
- [`type-enum-states`](rules/type-enum-states.md) - Use enums for mutually exclusive states
- [`type-option-nullable`](rules/type-option-nullable.md) - Use `Option<T>` for values that might not exist
- [`type-result-fallible`](rules/type-result-fallible.md) - Use `Result<T, E>` for operations that can fail
- [`type-phantom-marker`](rules/type-phantom-marker.md) - Use `PhantomData` to express type relationships without runtime cost
- [`type-never-diverge`](rules/type-never-diverge.md) - Use `!` (never type) for functions that never return
- [`type-generic-bounds`](rules/type-generic-bounds.md) - Add trait bounds only where needed, prefer where clauses for readability
- [`type-no-stringly`](rules/type-no-stringly.md) - Avoid stringly-typed APIs; use enums, newtypes, or validated types
- [`type-repr-transparent`](rules/type-repr-transparent.md) - Use `#[repr(transparent)]` for newtypes in FFI contexts
- [`type-deref-coercion`](rules/type-deref-coercion.md) - Implement `Deref`/`DerefMut` only for smart-pointer and transparent wrapper types
- [`type-display-vs-debug`](rules/type-display-vs-debug.md) - Use `Display` for user-facing output and `Debug` for diagnostics; never swap them
- [`type-numeric-fmt`](rules/type-numeric-fmt.md) - Implement `LowerHex`, `UpperHex`, `Octal`, and `Binary` for numeric newtypes
- [`type-unicode-length`](rules/type-unicode-length.md) - Define whether text limits count bytes, scalar values, or grapheme clusters

### 11. Trait & Generics Design (MEDIUM)

- [`trait-associated-type-vs-generic`](rules/trait-associated-type-vs-generic.md) - Use an associated type when each impl has exactly one output type; use a generic parameter when a type can implement the trait for many input types
- [`trait-blanket-impl`](rules/trait-blanket-impl.md) - Use a blanket impl `impl<T: Bound> Trait for T` to give behaviour to every type that satisfies a bound
- [`trait-coherence-newtype`](rules/trait-coherence-newtype.md) - Respect the orphan rule; wrap a foreign type in a newtype to implement a foreign trait on it
- [`trait-default-methods`](rules/trait-default-methods.md) - Define a trait in terms of a few required methods plus defaulted ones built on top of them
- [`trait-dyn-vs-generic`](rules/trait-dyn-vs-generic.md) - Choose concrete types, enums, generics, or `dyn Trait` from the substitution and ownership contract
- [`trait-object-safety`](rules/trait-object-safety.md) - Keep a trait dyn-compatible (object-safe) when you need `dyn Trait`
- [`trait-ord-consistent`](rules/trait-ord-consistent.md) - Keep `Ord`, `PartialOrd`, `Eq`, and `PartialEq` consistent

### 12. Conversions (MEDIUM)

- [`conv-tryfrom-fallible`](rules/conv-tryfrom-fallible.md) - Implement `TryFrom` for fallible conversions instead of ad-hoc conversion functions
- [`conv-fromstr-parsing`](rules/conv-fromstr-parsing.md) - Implement `FromStr` to enable `str::parse` for string-to-type conversions
- [`conv-asmut-mutable`](rules/conv-asmut-mutable.md) - Accept `impl AsMut<T>` for flexible mutable borrowed inputs instead of concrete mutable references

### 13. Const & Compile-Time (MEDIUM)

- [`const-block`](rules/const-block.md) - Use inline `const { }` blocks for compile-time evaluation and assertions
- [`const-fn`](rules/const-fn.md) - Make functions `const fn` when they can run at compile time
- [`const-generics`](rules/const-generics.md) - Parameterize over values with const generics `<const N: usize>`
- [`const-vs-static`](rules/const-vs-static.md) - Use `const` for an inlined value and `static` for a single addressed instance
- [`const-named-magic`](rules/const-named-magic.md) - Give production magic numbers a named `const` and a comment that says why that value

### 14. Serde (MEDIUM)

- [`serde-rename-all`](rules/serde-rename-all.md) - Match the external naming convention with `#[serde(rename_all = ...)]`
- [`serde-default-compat`](rules/serde-default-compat.md) - Use `#[serde(default)]` for optional and backward-compatible fields
- [`serde-skip-empty`](rules/serde-skip-empty.md) - Omit empty fields only when the wire contract equates empty and absent
- [`serde-flatten`](rules/serde-flatten.md) - Inline nested structs or capture extra keys with `#[serde(flatten)]`
- [`serde-enum-representation`](rules/serde-enum-representation.md) - Choose enum tagging deliberately: externally, internally, adjacently tagged, or untagged
- [`serde-deny-unknown-fields`](rules/serde-deny-unknown-fields.md) - Reject unexpected keys with `#[serde(deny_unknown_fields)]`
- [`serde-custom-with`](rules/serde-custom-with.md) - Customize a field's (de)serialization with `with` / `serialize_with` / `deserialize_with`
- [`serde-try-from-validate`](rules/serde-try-from-validate.md) - Validate while deserializing with `#[serde(try_from = "Raw")]`

### 15. Pattern Matching (MEDIUM)

- [`pat-let-else`](rules/pat-let-else.md) - Use `let ... else` for early-return pattern extraction
- [`pat-matches-macro`](rules/pat-matches-macro.md) - Use `matches!()` for boolean pattern tests
- [`pat-if-let-chains`](rules/pat-if-let-chains.md) - Use `if let` chains to combine pattern bindings and conditions
- [`pat-exhaustive-enum`](rules/pat-exhaustive-enum.md) - Match owned enums exhaustively; avoid catch-all `_` that hides new variants
- [`pat-at-bindings`](rules/pat-at-bindings.md) - Use `@` bindings to capture a value while matching it against a pattern
- [`pat-if-let-guards`](rules/pat-if-let-guards.md) - Use `if let` match guards to bind data needed only by one arm

### 16. Macros (MEDIUM)

- [`macro-prefer-functions`](rules/macro-prefer-functions.md) - Reach for a macro only when a function or generic cannot express it
- [`macro-rules-hygiene`](rules/macro-rules-hygiene.md) - Rely on `macro_rules!` hygiene and use `$crate` for paths to your crate's items
- [`macro-fragment-specifiers`](rules/macro-fragment-specifiers.md) - Capture with precise fragment specifiers, not raw `:tt`, where you can
- [`macro-export-crate-path`](rules/macro-export-crate-path.md) - Export declarative macros with `#[macro_export]` and a clean import path
- [`macro-private-helpers`](rules/macro-private-helpers.md) - Hide macro-generated helper items behind a `#[doc(hidden)] pub mod __private`
- [`macro-proc-two-crate`](rules/macro-proc-two-crate.md) - Put procedural macros in a dedicated `proc-macro = true` crate and re-export from the facade
- [`macro-proc-syn-quote`](rules/macro-proc-syn-quote.md) - Build procedural macros with `syn`, `quote`, and `proc-macro2`
- [`macro-proc-error-spans`](rules/macro-proc-error-spans.md) - Report proc-macro errors as spanned compile errors, never by panicking
- [`macro-no-rewrite-item`](rules/macro-no-rewrite-item.md) - Do not let a macro change an item's kind, signature, or async-ness from what the source shows
- [`macro-declarative-before-proc`](rules/macro-declarative-before-proc.md) - Prefer `macro_rules!` over a procedural macro whenever the transform can be written by example
- [`macro-no-implied-items`](rules/macro-no-implied-items.md) - Do not let a macro invent extra items the caller never wrote, especially public types

### 17. Closures (MEDIUM)

- [`closure-fn-trait-bounds`](rules/closure-fn-trait-bounds.md) - Require the least restrictive `Fn` trait a callback needs (`FnOnce` ⊇ `FnMut` ⊇ `Fn`)
- [`closure-impl-fn-return`](rules/closure-impl-fn-return.md) - Return closures as `impl Fn`/`FnMut`/`FnOnce`, not `Box<dyn Fn>`
- [`closure-move-capture`](rules/closure-move-capture.md) - Use `move` for closures that outlive the current scope; clone before `move` to keep the original
- [`closure-static-vs-dyn`](rules/closure-static-vs-dyn.md) - Accept `impl Fn` (generic) for hot callbacks; use `&dyn Fn`/`Box<dyn Fn>` to cut code size or to store them
- [`closure-disjoint-capture`](rules/closure-disjoint-capture.md) - Capture only what you use; lean on edition-2021 disjoint closure captures

### 18. Collections (MEDIUM)

- [`coll-binaryheap`](rules/coll-binaryheap.md) - Use `BinaryHeap` for a priority queue or repeated max-extraction
- [`coll-map-choice`](rules/coll-map-choice.md) - Pick the map by access pattern: `HashMap` (fast, unordered), `BTreeMap` (sorted / range queries), `IndexMap` (insertion order)
- [`coll-seq-choice`](rules/coll-seq-choice.md) - Default to `Vec`; use `VecDeque` for queue/deque behaviour; avoid `LinkedList`
- [`coll-set-membership`](rules/coll-set-membership.md) - Use `HashSet`/`BTreeSet` for membership tests and dedup, not linear `Vec::contains`

### 19. Naming Conventions (MEDIUM)

- [`name-types-camel`](rules/name-types-camel.md) - Use `UpperCamelCase` for types, traits, and enum names
- [`name-variants-camel`](rules/name-variants-camel.md) - Use `UpperCamelCase` for enum variants
- [`name-funcs-snake`](rules/name-funcs-snake.md) - Use `snake_case` for functions, methods, variables, and modules
- [`name-consts-screaming`](rules/name-consts-screaming.md) - Use `SCREAMING_SNAKE_CASE` for constants and statics
- [`name-lifetime-short`](rules/name-lifetime-short.md) - Use short, conventional lifetime names: `'a`, `'b`, `'de`, `'src`
- [`name-type-param-single`](rules/name-type-param-single.md) - Use single uppercase letters for type parameters: `T`, `E`, `K`, `V`
- [`name-as-free`](rules/name-as-free.md) - `as_` prefix: free reference conversion
- [`name-to-expensive`](rules/name-to-expensive.md) - Use `to_` prefix for expensive conversions that allocate or compute
- [`name-into-ownership`](rules/name-into-ownership.md) - Use `into_` prefix for ownership-consuming conversions
- [`name-no-get-prefix`](rules/name-no-get-prefix.md) - Omit get_ prefix for simple getters
- [`name-is-has-bool`](rules/name-is-has-bool.md) - Use `is_`, `has_`, `can_`, `should_` prefixes for boolean-returning methods
- [`name-iter-convention`](rules/name-iter-convention.md) - Use iter/iter_mut/into_iter for iterator methods
- [`name-iter-method`](rules/name-iter-method.md) - Name iterator methods `iter()`, `iter_mut()`, and `into_iter()` consistently
- [`name-iter-type-match`](rules/name-iter-type-match.md) - Name iterator types after their source method
- [`name-acronym-word`](rules/name-acronym-word.md) - Treat acronyms as words in identifiers: `HttpServer`, not `HTTPServer`
- [`name-crate-no-rs`](rules/name-crate-no-rs.md) - Don't suffix crate names with `-rs` or `-rust`
- [`name-no-weasel`](rules/name-no-weasel.md) - Drop empty role words like `Service`, `Manager`, and `Factory` from type names
- [`name-short-items`](rules/name-short-items.md) - Keep item names to about two short words; drop crate prefixes and lean on familiar abbreviations

### 20. Testing (MEDIUM)

- [`test-cfg-test-module`](rules/test-cfg-test-module.md) - Put unit tests in `#[cfg(test)] mod tests { }` within each module
- [`test-use-super`](rules/test-use-super.md) - Use `use super::*;` in test modules to access parent module items
- [`test-integration-dir`](rules/test-integration-dir.md) - Put integration tests in the `tests/` directory
- [`test-descriptive-names`](rules/test-descriptive-names.md) - Use descriptive test names that explain what is being tested
- [`test-arrange-act-assert`](rules/test-arrange-act-assert.md) - Structure tests with clear Arrange, Act, Assert sections
- [`test-proptest-properties`](rules/test-proptest-properties.md) - Use proptest for property-based testing
- [`test-mockall-mocking`](rules/test-mockall-mocking.md) - Use mockall for trait mocking
- [`test-mock-traits`](rules/test-mock-traits.md) - Put nondeterministic system effects behind a crate-owned native/test backend and return the test controller with the service
- [`test-fixture-raii`](rules/test-fixture-raii.md) - Use RAII pattern (Drop trait) for automatic test cleanup
- [`test-tokio-async`](rules/test-tokio-async.md) - Use `#[tokio::test]` for async tests
- [`test-should-panic`](rules/test-should-panic.md) - Use `#[should_panic]` to test that code panics as expected
- [`test-criterion-bench`](rules/test-criterion-bench.md) - Use a statistical harness such as Criterion or Divan for repeatable benchmarks
- [`test-doctest-examples`](rules/test-doctest-examples.md) - Keep documentation examples as executable doctests
- [`test-loom-concurrency`](rules/test-loom-concurrency.md) - Use bounded `loom` models to explore lock-free and concurrent code
- [`test-snapshot-testing`](rules/test-snapshot-testing.md) - Use snapshot testing (insta) for complex or serialized output
- [`test-no-tautology`](rules/test-no-tautology.md) - Assert a property or observable outcome, not a constant restated from the source
- [`test-util-feature`](rules/test-util-feature.md) - Put safe testing utilities behind an additive feature; never use a feature to weaken a production invariant
- [`test-observable-coverage`](rules/test-observable-coverage.md) - Cover observable behavior and failure modes so refactors can proceed without implementation-shaped tests
- [`test-http-blackbox`](rules/test-http-blackbox.md) - Test HTTP behavior through the production router and a real ephemeral listener

### 21. Documentation (MEDIUM)

- [`doc-all-public`](rules/doc-all-public.md) - Document all public items with `///` doc comments
- [`doc-module-inner`](rules/doc-module-inner.md) - Use `//!` for module-level documentation
- [`doc-examples-section`](rules/doc-examples-section.md) - Include `# Examples` with runnable code
- [`doc-errors-section`](rules/doc-errors-section.md) - Include `# Errors` section for fallible functions
- [`doc-panics-section`](rules/doc-panics-section.md) - Include `# Panics` section for functions that can panic
- [`doc-safety-section`](rules/doc-safety-section.md) - Document every caller or implementor obligation of unsafe APIs
- [`doc-question-mark`](rules/doc-question-mark.md) - Use `?` in examples, not `.unwrap()`
- [`doc-hidden-setup`](rules/doc-hidden-setup.md) - Use `# ` prefix to hide example setup code
- [`doc-intra-links`](rules/doc-intra-links.md) - Use intra-doc links to reference types and items
- [`doc-link-types`](rules/doc-link-types.md) - Use intra-doc links to connect related types and functions
- [`doc-cargo-metadata`](rules/doc-cargo-metadata.md) - Fill `Cargo.toml` metadata for published crates
- [`doc-crate-readme`](rules/doc-crate-readme.md) - Unify the README and crate root docs with `#![doc = include_str!("../README.md")]`
- [`doc-first-sentence`](rules/doc-first-sentence.md) - Write the first rustdoc sentence as one short standalone line — about fifteen words — that still makes sense in the module index
- [`doc-inline-reexport`](rules/doc-inline-reexport.md) - Inline an owned re-export when rustdoc would otherwise show only a forwarding link
- [`doc-canonical-sections`](rules/doc-canonical-sections.md) - Structure public API docs as summary, details, examples, errors, panics, safety, and abort behavior where each applies
- [`doc-no-meta-design`](rules/doc-no-meta-design.md) - Document the shipped crate for users; keep design history and process notes out of rustdoc

### 22. Observability (MEDIUM)

- [`obs-tracing-over-log`](rules/obs-tracing-over-log.md) - Use `tracing` for structured, span-aware diagnostics instead of `println!` or bare `log`
- [`obs-library-facade`](rules/obs-library-facade.md) - Libraries emit through the tracing/log facade and never install a subscriber
- [`obs-structured-fields`](rules/obs-structured-fields.md) - Record structured key-value fields, not values interpolated into the message string
- [`obs-instrument-spans`](rules/obs-instrument-spans.md) - Use `#[tracing::instrument]` and spans to attach context to async tasks and requests
- [`obs-levels-filter`](rules/obs-levels-filter.md) - Use log levels meaningfully and filter with `EnvFilter` / `RUST_LOG`
- [`obs-error-chain`](rules/obs-error-chain.md) - Log errors with their full source chain, and log each error exactly once
- [`obs-no-sensitive-data`](rules/obs-no-sensitive-data.md) - Never log secrets or PII; redact or skip them
- [`obs-named-events`](rules/obs-named-events.md) - Give telemetry a stable event name (and a message template) so releases stay queryable
- [`obs-request-correlation`](rules/obs-request-correlation.md) - Open one request span at the HTTP edge and propagate a non-sensitive correlation ID through all downstream work

### 23. Performance Patterns (MEDIUM)

- [`perf-iter-over-index`](rules/perf-iter-over-index.md) - Prefer iterators over manual indexing
- [`perf-iter-lazy`](rules/perf-iter-lazy.md) - Keep iterators lazy, collect only when needed
- [`perf-collect-once`](rules/perf-collect-once.md) - Don't collect intermediate iterators
- [`perf-entry-api`](rules/perf-entry-api.md) - Use entry API for map insert-or-update
- [`perf-drain-reuse`](rules/perf-drain-reuse.md) - Use drain to reuse allocations
- [`perf-extend-batch`](rules/perf-extend-batch.md) - Use extend for batch insertions
- [`perf-chain-avoid`](rules/perf-chain-avoid.md) - Avoid chain in hot loops
- [`perf-collect-into`](rules/perf-collect-into.md) - Use collect_into for reusing containers
- [`perf-black-box-bench`](rules/perf-black-box-bench.md) - Use `std::hint::black_box` to reduce benchmark optimizer artifacts
- [`perf-release-profile`](rules/perf-release-profile.md) - Treat release profiles as measured artifact policy, not a universal max-optimization preset
- [`perf-profile-first`](rules/perf-profile-first.md) - Profile before optimizing
- [`perf-ahash`](rules/perf-ahash.md) - Change hashers only after profiling and an explicit key-threat analysis
- [`perf-io-buffering`](rules/perf-io-buffering.md) - Wrap `Read`/`Write` in `BufReader`/`BufWriter` for many small operations
- [`perf-global-allocator`](rules/perf-global-allocator.md) - Pick the process global allocator on purpose in application crates; leave libraries on the system default
- [`perf-batch-throughput`](rules/perf-batch-throughput.md) - Optimize for items finished per CPU cycle with batches, independent slices, and no idle spinning

### 24. Project Structure (LOW)

- [`proj-lib-main-split`](rules/proj-lib-main-split.md) - Keep `main.rs` minimal, logic in `lib.rs`
- [`proj-mod-by-feature`](rules/proj-mod-by-feature.md) - Organize modules by feature, not type
- [`proj-flat-small`](rules/proj-flat-small.md) - Keep small projects flat
- [`proj-mod-rs-dir`](rules/proj-mod-rs-dir.md) - Use mod.rs for multi-file modules
- [`proj-pub-crate-internal`](rules/proj-pub-crate-internal.md) - Use pub(crate) for internal APIs
- [`proj-pub-super-parent`](rules/proj-pub-super-parent.md) - Use pub(super) for parent-only visibility
- [`proj-pub-use-reexport`](rules/proj-pub-use-reexport.md) - Give each owned item one public path; let callers import foreign types from their defining crate
- [`proj-prelude-module`](rules/proj-prelude-module.md) - Prefer named imports; provide a curated prelude only when a cohesive trait-heavy API needs one
- [`proj-bin-dir`](rules/proj-bin-dir.md) - Put multiple binaries in src/bin/
- [`proj-workspace-large`](rules/proj-workspace-large.md) - Use workspaces for large projects
- [`proj-workspace-deps`](rules/proj-workspace-deps.md) - Use workspace dependency inheritance for consistent versions across crates
- [`proj-feature-additive`](rules/proj-feature-additive.md) - Design Cargo features to be strictly additive
- [`proj-msrv-declare`](rules/proj-msrv-declare.md) - Declare `rust-version` (MSRV) in Cargo.toml and test it in CI
- [`proj-build-rs-minimal`](rules/proj-build-rs-minimal.md) - Keep `build.rs` minimal, deterministic, and idempotent
- [`proj-no-glob-reexport`](rules/proj-no-glob-reexport.md) - Re-export public items by name; do not `pub use foo::*` across modules or crates
- [`proj-avoid-statics`](rules/proj-avoid-statics.md) - Do not store mutable or process-identity state in `static`; pass it in. Reserve `static` for immutable tables
- [`proj-works-out-of-box`](rules/proj-works-out-of-box.md) - Default features must `cargo build` on tier-1 targets with only the Rust toolchain — no extra packages, env vars, or generated-at-install steps
- [`proj-latest-edition`](rules/proj-latest-edition.md) - Create new crates and workspaces on the latest stable edition (2024 today)
- [`proj-split-crates`](rules/proj-split-crates.md) - Extract independently useful modules into crates; join them again only as a thin umbrella
- [`proj-schema-migrations`](rules/proj-schema-migrations.md) - Treat database migrations as ordered source artifacts and prove they build the production schema from empty
- [`proj-typed-config`](rules/proj-typed-config.md) - Deserialize layered configuration into typed values, validate it once at startup, and keep secrets out of source
- [`proj-thin-vertical-slice`](rules/proj-thin-vertical-slice.md) - Deliver the smallest end-to-end user journey before deepening any one layer
- [`proj-continuous-delivery`](rules/proj-continuous-delivery.md) - Keep the protected mainline releasable and make deployment consume the exact admitted artifact
- [`proj-reproducible-runtime`](rules/proj-reproducible-runtime.md) - Build a pinned release artifact in one stage and run it in a minimal, non-secret runtime image
- [`proj-stable-toolchain`](rules/proj-stable-toolchain.md) - Build and run production applications on a pinned stable toolchain and test upgrades continuously
- [`proj-stateless-process`](rules/proj-stateless-process.md) - Keep durable application state outside individual service processes
- [`proj-cfg-select`](rules/proj-cfg-select.md) - Use `cfg_select!` for one-of-many conditional items or expressions

### 25. FFI & Interop (LOW)

- [`ffi-logic-in-core`](rules/ffi-logic-in-core.md) - Keep business logic in a safe core crate; limit the `*-ffi` crate to translating pointers and status codes
- [`ffi-sys-vs-ffi-name`](rules/ffi-sys-vs-ffi-name.md) - Name import wrappers `*-sys` and export shims `*-ffi`
- [`ffi-native-escape-hatch`](rules/ffi-native-escape-hatch.md) - Give native-handle wrappers `from_native` / `into_native` / `as_native` so FFI code can cross the boundary without leaking the raw type everywhere
- [`ffi-sys-crate-builds`](rules/ffi-sys-crate-builds.md) - Keep `-sys` crates hermetic: build verifiable vendored sources with Rust tooling and offer static or dynamic loading
- [`ffi-dll-portable-state`](rules/ffi-dll-portable-state.md) - Share only portable, repr-stable values across Rust dynamic libraries; keep allocations, statics, TLS, and TypeId local to the DLL that created them

### 26. Clippy & Linting (LOW)

- [`lint-deny-correctness`](rules/lint-deny-correctness.md) - `#![deny(clippy::correctness)]`
- [`lint-warn-suspicious`](rules/lint-warn-suspicious.md) - Enable clippy::suspicious for likely bugs
- [`lint-warn-style`](rules/lint-warn-style.md) - Enable clippy::style for idiomatic code
- [`lint-warn-complexity`](rules/lint-warn-complexity.md) - Enable clippy::complexity for simpler code
- [`lint-warn-perf`](rules/lint-warn-perf.md) - Enable `clippy::perf` as a review signal, then verify semantic and measured impact
- [`lint-pedantic-selective`](rules/lint-pedantic-selective.md) - Enable clippy::pedantic selectively
- [`lint-missing-docs`](rules/lint-missing-docs.md) - Warn on missing documentation for public items
- [`lint-unsafe-doc`](rules/lint-unsafe-doc.md) - Require a local proof for every unsafe operation
- [`lint-cargo-metadata`](rules/lint-cargo-metadata.md) - Enable clippy::cargo for published crates
- [`lint-rustfmt-check`](rules/lint-rustfmt-check.md) - Run cargo fmt --check in CI
- [`lint-workspace-lints`](rules/lint-workspace-lints.md) - Configure lints at workspace level for consistent enforcement
- [`lint-cfg-check`](rules/lint-cfg-check.md) - Enable `unexpected_cfgs` and declare known cfgs to catch feature-gate typos
- [`lint-clippy-nursery-selected`](rules/lint-clippy-nursery-selected.md) - Enable high-value `clippy::nursery` lints selectively, not the whole group
- [`lint-expect-override`](rules/lint-expect-override.md) - Prefer `#[expect(...)]` over `#[allow(...)]` when silencing a lint at an item
- [`lint-static-verification`](rules/lint-static-verification.md) - Gate compiler and Clippy lints, formatting, dependency audits, feature combinations, unused dependencies, and unsafe-code checks in CI
- [`lint-warnings-deny-config`](rules/lint-warnings-deny-config.md) - Prefer Cargo `[build] warnings = "deny"` over `RUSTFLAGS=-Dwarnings` for rustc CI

### 27. Anti-patterns (REFERENCE)

- [`anti-unwrap-abuse`](rules/anti-unwrap-abuse.md) - Do not turn expected input, dependency, or lifecycle failures into panics
- [`anti-expect-lazy`](rules/anti-expect-lazy.md) - Don't use expect for recoverable errors
- [`anti-clone-excessive`](rules/anti-clone-excessive.md) - Don't clone when borrowing works
- [`anti-lock-across-await`](rules/anti-lock-across-await.md) - Don't hold synchronous locks or incidental shared-state guards across await points
- [`anti-string-for-str`](rules/anti-string-for-str.md) - Don't accept &String when &str works
- [`anti-vec-for-slice`](rules/anti-vec-for-slice.md) - Don't accept &Vec<T> when &[T] works
- [`anti-index-over-iter`](rules/anti-index-over-iter.md) - Don't use indexing when iterators work
- [`anti-panic-expected`](rules/anti-panic-expected.md) - Don't panic on expected or recoverable errors
- [`anti-empty-catch`](rules/anti-empty-catch.md) - Don't silently ignore errors
- [`anti-over-abstraction`](rules/anti-over-abstraction.md) - Don't over-abstract with excessive generics
- [`anti-premature-optimize`](rules/anti-premature-optimize.md) - Don't optimize before profiling
- [`anti-type-erasure`](rules/anti-type-erasure.md) - Don't erase a concrete type when `impl Trait`, a generic, or an enum keeps the contract honest
- [`anti-format-hot-path`](rules/anti-format-hot-path.md) - Don't use format! in hot paths
- [`anti-collect-intermediate`](rules/anti-collect-intermediate.md) - Don't collect intermediate iterators
- [`anti-stringly-typed`](rules/anti-stringly-typed.md) - Don't use strings where enums or newtypes would provide type safety
- [`anti-transliterated-port`](rules/anti-transliterated-port.md) - Port domain behavior into Rust; do not copy the source language's types, errors, or runtime architecture

---

## Recommended Cargo.toml Settings

```toml
[profile.release]
opt-level = 3
lto = "fat"
codegen-units = 1
panic = "abort"
strip = true

[profile.bench]
inherits = "release"
debug = true
strip = false

[profile.dev]
opt-level = 0
debug = true

[profile.dev.package."*"]
opt-level = 3  # Optimize dependencies in dev
```

---

## How to Use

This skill provides rule identifiers for quick reference. When generating or reviewing Rust code:

1. **Check relevant category** based on task type
2. **Apply rules** with matching prefix
3. **Prioritize** CRITICAL > HIGH > MEDIUM > LOW
4. **Read rule files** in `rules/` for detailed examples

### Rule Application by Task

| Task | Primary Categories |
|------|-------------------|
| New function | `own-`, `err-`, `name-`, `pat-` |
| New struct/API | `api-`, `type-`, `conv-`, `doc-` |
| Async code | `async-`, `own-` |
| Concurrency / parallelism | `conc-`, `async-`, `own-` |
| Unsafe code | `unsafe-`, `type-`, `test-`, `ffi-` |
| Error handling | `err-`, `api-`, `pat-` |
| Type conversions | `conv-`, `api-` |
| Serialization (serde) | `serde-`, `type-`, `api-` |
| Numeric / arithmetic | `num-`, `type-` |
| Macros / code generation | `macro-`, `anti-` |
| Closures / callbacks | `closure-`, `type-` |
| Logging / observability | `obs-`, `err-` |
| Memory optimization | `mem-`, `own-`, `perf-` |
| Performance tuning | `opt-`, `mem-`, `perf-` |
| FFI / C interop | `ffi-`, `unsafe-`, `type-` |
| Code review | `anti-`, `lint-` |

---

## Sources & Attribution

This skill is an independent synthesis of official Rust guidance, well-known books, and patterns from widely-used crates. It is not affiliated with or endorsed by the Rust project or any crate author; the text and code examples are original.

**Official Rust documentation**
- [The Rust Reference](https://doc.rust-lang.org/reference/)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- [The Rustonomicon](https://doc.rust-lang.org/nomicon/) (unsafe code)
- [Rust 2024 Edition Guide](https://doc.rust-lang.org/edition-guide/rust-2024/)
- [The Cargo Book](https://doc.rust-lang.org/cargo/)
- [Standard library docs](https://doc.rust-lang.org/std/) and [release notes](https://doc.rust-lang.org/releases.html)

**Books & guides**
- [The Rust Performance Book](https://nnethercote.github.io/perf-book/) — Nicholas Nethercote
- [Rust Design Patterns](https://rust-unofficial.github.io/patterns/) — rust-unofficial
- [Rust Atomics and Locks](https://marabos.nl/atomics/) — Mara Bos
- [Effective Rust](https://effective-rust.com/) — David Drysdale
- [Microsoft Pragmatic Rust Guidelines](https://microsoft.github.io/rust-guidelines/) (v2026.6, [microsoft/rust-guidelines](https://github.com/microsoft/rust-guidelines)) — production-oriented library, FFI, and correctness guidance

**Tooling**
- [Clippy lint documentation](https://rust-lang.github.io/rust-clippy/)
- [Miri](https://github.com/rust-lang/miri)

**Real-world codebases studied for idioms**
- ripgrep, tokio, serde, clap, polars, axum, cargo, hyper, bevy, rayon, and dtolnay's crates (thiserror, anyhow, syn)

This project is MIT-licensed. Referenced upstream materials remain under their own licenses (the official Rust docs and API Guidelines are dual MIT / Apache-2.0).
