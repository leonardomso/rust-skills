# opt-codegen-units

> Measure codegen-unit count as a build-throughput and runtime trade-off

## Why It Matters

Cargo can split a crate into multiple code generation units so LLVM work runs in parallel. Fewer units expose more of one crate to a single optimization unit but reduce code-generation parallelism and may increase peak memory. The final result also depends on LTO, incremental compilation, target, crate graph, and compiler version. `codegen-units = 1` is a candidate to benchmark, not a universal production setting.

## Bad

```toml
[profile.release]
codegen-units = 1
lto = "fat"
```

This labels the most serial, resource-intensive combination as correct without measuring build cost or deployed behavior.

## Good

```toml
[profile.release-cgu1-candidate]
inherits = "release"
codegen-units = 1
```

Compare it with the release default and one intermediate candidate while holding every other input constant:

```toml
[profile.release-cgu4-candidate]
inherits = "release"
codegen-units = 4
```

Use named profiles so benchmark and artifact evidence says exactly which code-generation policy produced the bytes.

## Contract

- More codegen units can increase parallelism and reduce wall time on a machine with available CPU and memory, but scheduling and crate shape determine the result.
- One codegen unit gives LLVM one unit for the crate; it does not provide whole-program visibility unless the selected LTO mode does so.
- Fewer units do not guarantee faster runtime or a smaller binary. They can change inlining, layout, compile time, and peak memory in either direction.
- Cargo defaults differ for incremental and non-incremental profiles; inspect the effective profile rather than copying a stale constant.
- A library's own profile settings are ignored when it is built as a dependency; the workspace/root application owns the final profile.

## Representative Measurement

```bash
cargo build --locked --profile release-cgu1-candidate
cargo test --locked --profile release-cgu1-candidate
cargo bench --profile release-cgu1-candidate
```

Record clean build time, incremental build time if relevant, linker/codegen peak memory, artifact size, startup, throughput, and tail latency. Run enough samples on controlled hosts to separate noise from a material change. Preserve toolchain, target CPU, lockfile, and LTO mode with the record.

## Development And CI

Do not equate “CI” with a low-quality artifact profile. Admission must test the exact candidate that will be promoted. A separate fast feedback job may use a cheaper profile, but it cannot replace final-profile tests. Likewise, setting `codegen-units = 256` in development can make some builds slower or more memory-intensive; use the Cargo default until measurement shows a better local policy.

## Failure Behavior

- Reject a candidate that exceeds bounded CI memory or wall time even when a microbenchmark improves.
- Reject a runtime optimization that regresses the product's stated latency, throughput, size, or energy objective.
- Treat compiler, linker, target, LTO, and dependency changes as reasons to re-run the comparison.
- Promote the tested digest. Rebuilding the same source with a different codegen-unit setting is a different candidate.

## See Also

- [opt-lto-release](./opt-lto-release.md) - benchmark the interaction with LTO
- [perf-release-profile](./perf-release-profile.md) - make the whole profile explicit
- [opt-pgo-profile](./opt-pgo-profile.md) - use representative profile data
- [perf-profile-first](./perf-profile-first.md) - measure the actual objective
