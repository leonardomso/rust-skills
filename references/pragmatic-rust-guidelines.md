# Pragmatic Rust Guidelines crosswalk

Microsoft publishes the [Pragmatic Rust Guidelines](https://microsoft.github.io/rust-guidelines/), a set of `M-*` guidelines for writing Rust at scale. The source is MIT licensed. Some of the guidelines are opinionated or tied to Microsoft's own projects, so this library does not adopt them wholesale.

This file is optional context. The rules in [`rules/`](../rules/) do not depend on it. It maps every Microsoft guideline to the rules here that cover it, so you can see what was adopted, what was already covered, and what was left out and why. If you want the Microsoft style in a project, read the entries marked `not adopted` or `partial` and follow the original guideline where it differs from our rules.

New rules adopted from this set were written in this library's own words and examples. Each one credits its source guideline in its `See Also` section.

## Status

- `adopted`: a new rule was added from this guideline.
- `covered`: an existing rule already says this.
- `partial`: an existing rule covers part of it.
- `not adopted`: no rule, with the reason given.


## Universal

| Guideline | Our rules | Status | Notes |
|---|---|---|---|
| M-UPSTREAM-GUIDELINES | [api-common-traits](../rules/api-common-traits.md), [name-types-camel](../rules/name-types-camel.md) | partial | Follow the official Rust API Guidelines and style guide. Our naming and API rules are drawn from them, but the full upstream set is not restated. |
| M-STATIC-VERIFICATION | [lint-rustfmt-check](../rules/lint-rustfmt-check.md), [lint-deny-correctness](../rules/lint-deny-correctness.md), [lint-warn-suspicious](../rules/lint-warn-suspicious.md), [unsafe-miri-ci](../rules/unsafe-miri-ci.md) | partial | rustc, clippy, rustfmt, and Miri are covered. cargo-audit and cargo-hack are not mentioned. |
| M-LINT-OVERRIDE-EXPECT | [lint-expect-over-allow](../rules/lint-expect-over-allow.md) | adopted | New rule. |
| M-PUBLIC-DEBUG | [api-common-traits](../rules/api-common-traits.md) | covered | Public types implement `Debug`. |
| M-PUBLIC-DISPLAY | [type-display-vs-debug](../rules/type-display-vs-debug.md), [api-common-traits](../rules/api-common-traits.md) | covered | Types meant to be read implement `Display`. |
| M-SMALLER-CRATES | [proj-workspace-large](../rules/proj-workspace-large.md) | partial | We recommend workspaces for large projects but do not say to split by default. |
| M-WEASEL-WORDS | [name-weasel-words](../rules/name-weasel-words.md) | adopted | New rule. |
| M-SHORT-NAMES | none | not adopted | Contested. Short names conflict with descriptive names in several of our rules, and there is no broad community consensus on a length limit. |
| M-REGULAR-FN | none | not adopted | Preferring free functions over associated functions runs against common Rust style (`Type::new`, `Type::from_*`), which our API rules follow. |
| M-DOCUMENTED-MAGIC | [name-consts-screaming](../rules/name-consts-screaming.md), [const-vs-static](../rules/const-vs-static.md) | partial | Named constants are covered. The requirement to document why a value was chosen is not. |
| M-LOG-STRUCTURED | [obs-structured-fields](../rules/obs-structured-fields.md) | covered | Structured fields over interpolated messages. |

## Libraries: interoperability

| Guideline | Our rules | Status | Notes |
|---|---|---|---|
| M-TYPES-SEND | [api-types-send](../rules/api-types-send.md) | adopted | New rule. |
| M-ESCAPE-HATCHES | none | not adopted | Specific to crates that wrap native handles. Too narrow for a general rule. |
| M-DONT-LEAK-TYPES | [api-dont-leak-types](../rules/api-dont-leak-types.md) | adopted | New rule. |
| M-FOREIGN-REEXPORTS | [api-dont-leak-types](../rules/api-dont-leak-types.md), [proj-pub-use-reexport](../rules/proj-pub-use-reexport.md) | partial | Our re-export rule covers re-exporting your own items. It does not forbid re-exporting foreign items, which `api-dont-leak-types` only discourages. |
| M-IMPL-ASREF | [api-impl-asref](../rules/api-impl-asref.md) | covered | Accept `impl AsRef<T>` where feasible. |
| M-IMPL-RANGEBOUNDS | [api-impl-rangebounds](../rules/api-impl-rangebounds.md) | adopted | New rule. |
| M-IMPL-IO | [api-sans-io](../rules/api-sans-io.md) | adopted | New rule. |

## Libraries: UX

| Guideline | Our rules | Status | Notes |
|---|---|---|---|
| M-SIMPLE-ABSTRACTIONS | [anti-over-abstraction](../rules/anti-over-abstraction.md), [type-generic-bounds](../rules/type-generic-bounds.md) | partial | We warn against needless generics but do not mandate hiding nested parametrized types. |
| M-AVOID-WRAPPERS | [own-slice-over-vec](../rules/own-slice-over-vec.md) | partial | Accepting `&str` and `&[T]` is covered. We do not discourage `Arc`, `Box`, or `Cow` in public signatures, since `own-arc-shared` and `own-cow-conditional` recommend them where they fit. |
| M-DI-HIERARCHY | [trait-dyn-vs-generic](../rules/trait-dyn-vs-generic.md) | partial | We say to choose static or dynamic dispatch deliberately. The strict ordering of types, then generics, then `dyn` is not adopted. |
| M-ERRORS-CANONICAL-STRUCTS | [err-thiserror-lib](../rules/err-thiserror-lib.md), [err-custom-type](../rules/err-custom-type.md) | not adopted | Our rules recommend error enums built with `thiserror`. Opaque situation-specific structs are a different, valid design; choose one per crate. |
| M-FROM-ERROR | [err-from-impl](../rules/err-from-impl.md) | covered | Implement `From` for owned error types. |
| M-INIT-BUILDER | [api-builder-pattern](../rules/api-builder-pattern.md), [api-builder-must-use](../rules/api-builder-must-use.md) | covered | Builders for complex construction. |
| M-INIT-CASCADED | [api-builder-pattern](../rules/api-builder-pattern.md) | partial | Builders are covered. Grouping many parameters into cascaded config types is not. |
| M-SERVICES-CLONE | [own-arc-shared](../rules/own-arc-shared.md) | not adopted | Cheap-to-clone service handles over `Arc<Inner>` are a design choice, not a general rule. |
| M-ESSENTIAL-FN-INHERENT | none | not adopted | No rule yet. Reasonable guidance, but not yet judged broad enough to add. |
| M-BALANCED-MODULES | [proj-mod-by-feature](../rules/proj-mod-by-feature.md), [proj-flat-small](../rules/proj-flat-small.md) | partial | We cover organizing by feature and keeping small projects flat, not module size balance. |
| M-NO-PRELUDE | [proj-prelude-module](../rules/proj-prelude-module.md) | not adopted | Directly conflicts with `proj-prelude-module`, which recommends a prelude for crates with many commonly used items. Pick one stance per project. |
| M-PARAMETER-CONSISTENCY | none | not adopted | Minor style guidance with no existing rule. |
| M-COLLECTION-TRAITS | [api-impl-fromiterator](../rules/api-impl-fromiterator.md), [name-iter-method](../rules/name-iter-method.md) | covered | Collections implement `FromIterator`, `Extend`, and `IntoIterator`. |
| M-ASYNC-FN | [async-fn-in-trait](../rules/async-fn-in-trait.md), [async-future-size](../rules/async-future-size.md) | partial | We use `async fn` throughout. The explicit rule to prefer it over `-> impl Future` has an exception documented in `async-future-size`. |

## Libraries: resilience

| Guideline | Our rules | Status | Notes |
|---|---|---|---|
| M-MOCKABLE-SYSCALLS | [test-mock-traits](../rules/test-mock-traits.md), [test-mockall-mocking](../rules/test-mockall-mocking.md) | partial | Mocking through traits is covered. The runtime-dispatch enum design for I/O types is not. |
| M-TEST-UTIL | [test-utils-feature-gated](../rules/test-utils-feature-gated.md) | adopted | New rule. |
| M-INTEGRATION-TESTS | [test-integration-dir](../rules/test-integration-dir.md) | covered | Integration tests live in `tests/`. |
| M-STRONG-TYPES | [type-newtype-ids](../rules/type-newtype-ids.md), [type-no-stringly](../rules/type-no-stringly.md) | partial | Newtypes and typed values are covered. The table mapping OS-facing strings to `PathBuf` and similar is not. |
| M-STRONG-TYPES-GUARD | [type-newtype-validated](../rules/type-newtype-validated.md), [api-parse-dont-validate](../rules/api-parse-dont-validate.md) | covered | Newtypes guard their invariants. |
| M-BUILD-RESULT | [api-builder-pattern](../rules/api-builder-pattern.md), [api-parse-dont-validate](../rules/api-parse-dont-validate.md) | partial | Validating at the end of construction follows from parse-don't-validate, but `build()` returning `Result` is not stated explicitly. |
| M-NO-GLOB-REEXPORTS | [api-no-glob-reexports](../rules/api-no-glob-reexports.md) | adopted | New rule. |
| M-AVOID-STATICS | [api-avoid-statics](../rules/api-avoid-statics.md) | adopted | New rule. |
| M-LOG-NOT-PRINT | [obs-tracing-over-log](../rules/obs-tracing-over-log.md) | covered | Use `tracing`, not `println!`. |

## Libraries: building

| Guideline | Our rules | Status | Notes |
|---|---|---|---|
| M-OOBE | [proj-build-rs-minimal](../rules/proj-build-rs-minimal.md) | partial | We keep `build.rs` minimal. Requiring that libraries build on all platforms without extra tools is not stated. |
| M-SYS-CRATES | [proj-build-rs-minimal](../rules/proj-build-rs-minimal.md) | not adopted | Specific to native `-sys` crates. |
| M-FEATURES-ADDITIVE | [proj-feature-additive](../rules/proj-feature-additive.md) | covered | Features only add functionality. |

## Macros

| Guideline | Our rules | Status | Notes |
|---|---|---|---|
| M-MACRO-LAST-RESORT | [macro-prefer-functions](../rules/macro-prefer-functions.md) | covered | Use a macro only when a function cannot do the job. |
| M-EXAMPLE-OVER-PROC | [macro-prefer-functions](../rules/macro-prefer-functions.md), [macro-proc-two-crate](../rules/macro-proc-two-crate.md) | partial | We prefer functions over macros but do not rank `macro_rules!` over proc macros. |
| M-MACROS-DONT-LIE | [macro-fragment-specifiers](../rules/macro-fragment-specifiers.md) | not adopted | Keeping macro call syntax faithful to the signature it generates is not covered. |
| M-MACRO-MAIN-CRATE | [macro-rules-hygiene](../rules/macro-rules-hygiene.md), [macro-export-crate-path](../rules/macro-export-crate-path.md) | partial | Using `$crate` for paths is covered. |
| M-MACRO-VERSION-PIN | [macro-pin-impl-crate](../rules/macro-pin-impl-crate.md) | adopted | New rule. |
| M-MACRO-HELPERS | [macro-private-helpers](../rules/macro-private-helpers.md) | covered | Hide macro helpers in a doc-hidden private module. |
| M-PROC-IMPL | [macro-proc-two-crate](../rules/macro-proc-two-crate.md) | covered | Separate crate for proc macro implementation. |
| M-PROC-IMPLIED-ITEMS | none | not adopted | Narrow proc-macro design advice. |

## Applications

| Guideline | Our rules | Status | Notes |
|---|---|---|---|
| M-APP-ERROR | [err-anyhow-app](../rules/err-anyhow-app.md) | covered | Applications may use `anyhow`. |
| M-MIMALLOC-APPS | [mem-global-allocator](../rules/mem-global-allocator.md) | adopted | Adopted as an optional, measure-first suggestion rather than a requirement. |
| M-TARGET-CPU | [opt-target-cpu](../rules/opt-target-cpu.md) | covered | Target the highest CPU the fleet guarantees. |

## FFI

| Guideline | Our rules | Status | Notes |
|---|---|---|---|
| M-ISOLATE-DLL-STATE | none | not adopted | Specific to Windows DLL and cross-library FFI designs. |
| M-FFI-TRANSLATES | [type-repr-transparent](../rules/type-repr-transparent.md) | not adopted | Architecture advice for FFI crates; our FFI coverage is limited to representation and unsafe syntax. |
| M-FFI-NAMING | none | not adopted | Naming convention for FFI crates specific to Microsoft projects. |

## Correctness

| Guideline | Our rules | Status | Notes |
|---|---|---|---|
| M-UNSAFE | [unsafe-safety-comment](../rules/unsafe-safety-comment.md), [unsafe-minimize-scope](../rules/unsafe-minimize-scope.md) | partial | Reasons and small scope are covered. 'Avoid unsafe where a safe alternative exists' is implied, not stated. |
| M-UNSAFE-IMPLIES-UB | [unsafe-sound-abstractions](../rules/unsafe-sound-abstractions.md) | adopted | Folded into the soundness rule. |
| M-UNSOUND | [unsafe-sound-abstractions](../rules/unsafe-sound-abstractions.md) | adopted | New rule. |
| M-PANIC-IS-STOP | [err-result-over-panic](../rules/err-result-over-panic.md), [err-result-over-panic](../rules/err-result-over-panic.md) | covered | Do not use panics for recoverable errors. |
| M-PANIC-ON-BUG | [err-expect-bugs-only](../rules/err-expect-bugs-only.md) | covered | Panic for detected bugs, return errors for expected failures. |
| M-PANIC-CONTINUATION | none | not adopted | No rule on `catch_unwind` yet. |
| M-PANIC-MESSAGE | [err-expect-bugs-only](../rules/err-expect-bugs-only.md), [err-lowercase-msg](../rules/err-lowercase-msg.md) | partial | Message style is covered; helpful panic messages are not stated on their own. |

## Performance

| Guideline | Our rules | Status | Notes |
|---|---|---|---|
| M-HOTPATH | [perf-profile-first](../rules/perf-profile-first.md), [test-criterion-bench](../rules/test-criterion-bench.md) | covered | Identify and profile hot paths. |
| M-THROUGHPUT | [perf-extend-batch](../rules/perf-extend-batch.md), [perf-profile-first](../rules/perf-profile-first.md) | partial | Batching is covered. Items-per-cycle as a primary metric is not. |
| M-YIELD-POINTS | [async-yield-points](../rules/async-yield-points.md) | adopted | New rule. |
| M-MEM-REUSE | [mem-reuse-collections](../rules/mem-reuse-collections.md), [mem-clone-from](../rules/mem-clone-from.md) | covered | Reuse allocations. |
| M-LOG-OVERHEAD | [obs-log-overhead](../rules/obs-log-overhead.md) | adopted | New rule. |
| M-AVOID-INDIRECTION | [opt-cache-friendly](../rules/opt-cache-friendly.md), [own-arc-shared](../rules/own-arc-shared.md) | partial | Cache layout is covered. The warning against reflexive nested `Arc` is not. |
| M-BOX-DST | [mem-boxed-slice](../rules/mem-boxed-slice.md) | covered | Boxed slices and strings for immutable data. |
| M-SHRINK-TO-FIT | [mem-shrink-to-fit](../rules/mem-shrink-to-fit.md) | adopted | New rule. |
| M-FAST-HASHER | [perf-ahash](../rules/perf-ahash.md) | covered | Use a faster hasher where DoS resistance is not needed. |
| M-INITIAL-CAPACITY | [mem-with-capacity](../rules/mem-with-capacity.md) | covered | Reserve capacity up front. |
| M-ASYNC-STACK-SIZE | [async-future-size](../rules/async-future-size.md) | adopted | New rule. |

## Project

| Guideline | Our rules | Status | Notes |
|---|---|---|---|
| M-CARGO-WORKSPACE | [proj-workspace-deps](../rules/proj-workspace-deps.md), [lint-workspace-lints](../rules/lint-workspace-lints.md) | covered | Common settings come from the workspace. |
| M-CRATES-IN-WORKSPACE | [proj-workspace-large](../rules/proj-workspace-large.md) | covered | Use a workspace for multi-crate projects. |
| M-CRATES-FLAT-FOLDER | none | not adopted | Directory layout preference without wide consensus. |
| M-LATEST-EDITION | [proj-msrv-declare](../rules/proj-msrv-declare.md) | partial | All examples in this library target the 2024 edition. A dedicated rule was judged too thin to add. |
| M-MSRV | [proj-msrv-declare](../rules/proj-msrv-declare.md) | partial | We say to declare an MSRV. The advice to raise it conservatively is not stated. |

## Documentation

| Guideline | Our rules | Status | Notes |
|---|---|---|---|
| M-MODULE-DOCS | [doc-module-inner](../rules/doc-module-inner.md) | covered | Document modules with `//!`. |
| M-FIRST-DOC-SENTENCE | [doc-first-sentence](../rules/doc-first-sentence.md) | adopted | New rule. |
| M-CANONICAL-DOCS | [doc-errors-section](../rules/doc-errors-section.md), [doc-panics-section](../rules/doc-panics-section.md), [doc-safety-section](../rules/doc-safety-section.md), [doc-examples-section](../rules/doc-examples-section.md) | covered | Canonical sections in doc comments. |
| M-DOC-INLINE | [api-no-glob-reexports](../rules/api-no-glob-reexports.md) | adopted | Covered as a section of `api-no-glob-reexports`. |

## AI

| Guideline | Our rules | Status | Notes |
|---|---|---|---|
| M-DESIGN-FOR-AI | none | not adopted | General design advice. This library is itself written for AI agents, so its rules already follow it in form. |
| M-SINGLE-ITEM-PATH | [proj-pub-use-reexport](../rules/proj-pub-use-reexport.md) | not adopted | Conflicts with the common pattern of re-exporting items at the crate root while keeping the module public. |
| M-NO-META-DESIGN-DOCUMENTATION | none | not adopted | Documentation style preference, not Rust-specific. |
| M-TAUTOLOGICAL-TESTS | [test-no-tautological](../rules/test-no-tautological.md) | adopted | New rule. |
| M-RUST-SHAPED | none | not adopted | Process advice for agents, not a coding rule. |
