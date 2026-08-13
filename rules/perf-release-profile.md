# perf-release-profile

> Treat release profiles as measured artifact policy, not a universal max-optimization preset

## Why It Matters

Cargo's release defaults are a reasonable general baseline. Changing LTO, codegen units, debug information, stripping, panic strategy, or size optimization changes build cost, runtime behavior, diagnostics, cache identity, and sometimes ABI/unwind behavior. There is no profile that is simultaneously fastest, smallest, cheapest to build, and easiest to operate. Benchmark representative workloads, record the exact profile with the artifact, and retain enough symbols to debug the deployed bytes.

## Bad

```toml
[profile.release]
opt-level = 3
lto = "fat"
codegen-units = 1
panic = "abort"
strip = true
```

This cargo-cult preset assumes fat LTO and one codegen unit improve the product, makes panic recovery impossible, and removes production diagnostics without evidence. It also changes every release consumer rather than defining a named, reviewed artifact policy.

## Good

```toml
# Workspace Cargo.toml
[profile.release-service]
inherits = "release"
debug = "line-tables-only"
strip = "none"

# Candidates below stay only after representative benchmark and binary-size
# evidence. Thin LTO is not automatically better for every workload.
lto = "thin"
codegen-units = 1
```

Build and benchmark the same named profile used for the candidate artifact:

```bash
cargo build --locked --profile release-service
cargo test --locked --profile release-service
cargo bench --profile release-service
```

Keep full or split debug information in a protected symbol artifact keyed to the exact executable digest. Do not rebuild later to recover symbols.

## Profile Decisions

| Setting | Decision to record |
|---|---|
| `opt-level` | Throughput/latency/size objective and representative benchmark |
| `lto` | `"off"` (none), `false` (thin-local when applicable), `"thin"`, or `"fat"`; build-time and runtime evidence |
| `codegen-units` | Parallel build cost versus cross-unit optimization evidence |
| `debug` / `split-debuginfo` | Symbolization and debugger support for every target |
| `strip` | Which copy retains symbols and how it is associated with the artifact digest |
| `panic` | Unwind, abort, FFI, task-isolation, and crash-restart contract |
| `overflow-checks` | Required arithmetic failure behavior; never change accidentally between tested and shipped profiles |

`panic = "abort"` can reduce some binary overhead, but it terminates the process on panic and prevents `catch_unwind`. It is a product reliability decision, not a generic performance switch. `strip = true` can reduce the shipped file but must not destroy the only symbols needed for crash analysis.

## Size-Oriented Profile

```toml
[profile.release-size]
inherits = "release"
opt-level = "z"
lto = "thin"
codegen-units = 1
debug = "line-tables-only"
strip = "none"
```

This is a candidate for a size-constrained artifact, not a promise that `"z"`, thin LTO, or one codegen unit produces the smallest output on every target. Compare compressed and resident size, startup, steady-state performance, and build memory. Keep the debug companion.

## Profiling Profile

```toml
[profile.profiling]
inherits = "release"
debug = true
strip = "none"
```

A profiling profile is useful only when it preserves the optimization choices whose behavior you are investigating. If it differs from production LTO, codegen units, target CPU, or panic strategy, label the evidence accordingly.

## Development Dependencies

```toml
[profile.dev.package."*"]
opt-level = 2
```

Per-package optimization can speed a workload dominated by slow unoptimized dependencies, but it also increases clean build time. Measure the developer loop before adopting it. Package overrides cannot set every profile key—for example, Cargo rejects `lto` and `panic` in a package override—so keep whole-artifact settings on the named profile.

## Failure Behavior

- A profile change creates a new candidate artifact and must pass the full test, benchmark, and rollout gates again.
- Benchmark regressions, excessive linker memory, missing symbols, or incompatible unwind behavior fail adoption; do not hide them by raising CI timeouts.
- Preserve a rollback artifact and its matching symbols. A rebuild from the same source is not the same promoted binary.
- Record compiler version, target, target features, profile, and dependency lock with the artifact digest.

## See Also

- [opt-lto-release](./opt-lto-release.md) - choose LTO mode from measurement
- [opt-codegen-units](./opt-codegen-units.md) - trade build parallelism for optimization deliberately
- [opt-pgo-profile](./opt-pgo-profile.md) - use representative profile-guided optimization
- [proj-reproducible-runtime](proj-reproducible-runtime.md) - promote the exact tested artifact
- [perf-profile-first](perf-profile-first.md) - measure before changing code generation
