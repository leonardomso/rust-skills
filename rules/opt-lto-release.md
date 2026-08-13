# opt-lto-release

> Benchmark LTO modes on final binaries; do not assume fat LTO wins

## Why It Matters

Link-time optimization can expose cross-codegen-unit and cross-crate optimization opportunities, but it increases link time and memory and can change runtime performance or binary size in either direction. Compiler version, target, codegen units, dependency graph, and workload all matter. Libraries do not control the final link profile; application owners choose and verify LTO on the complete artifact.

## Bad

```toml
[profile.release]
lto = "fat"
codegen-units = 1
panic = "abort"
strip = true
```

This mixes LTO with unrelated panic and symbol policies, declares fat LTO optimal without evidence, and makes rollback/debugging harder.

## Good

```toml
[profile.release-lto-candidate]
inherits = "release"
lto = "thin"
```

Compare that candidate with the unmodified release profile and, when justified by the product's unit-cost or latency objective, a separate fat-LTO candidate:

```toml
[profile.release-fat-lto-candidate]
inherits = "release"
lto = "fat"
codegen-units = 1
```

Use identical source, lockfile, toolchain, target features, benchmark inputs, and symbol policy. Record wall time, linker peak memory, artifact size, startup, throughput, tail latency, and the resulting binary digest.

## Cargo LTO Values

```toml
# Disable LTO.
lto = "off"

# Cargo's default. Performs thin-local LTO across local codegen units when
# codegen-units > 1 and opt-level > 0; otherwise performs no LTO.
lto = false

# Thin LTO across the dependency graph.
lto = "thin"

# Fat LTO across the dependency graph.
lto = "fat"
# `true` is an alias for `"fat"`.
```

`false` and `"off"` are deliberately different. Keep that distinction in reviews and generated configuration.

## Decision Contract

| Candidate | Expected trade-off to verify |
|---|---|
| `"off"` | Lowest LTO work, but not necessarily fastest build or largest binary |
| `false` | Cargo default thin-local behavior when applicable |
| `"thin"` | Cross-crate optimization with a scalable LTO design |
| `"fat"` | Broadest whole-graph analysis and usually the highest link resource cost |

Do not publish percentage gains or size rankings without the benchmark, target, compiler, and workload that produced them. Thin can match or beat fat; no LTO can win; codegen-units can interact with every result.

## Operational Requirements

- Apply LTO to final application artifacts, not as a library crate's claimed runtime guarantee.
- Keep debug/symbol artifacts associated with the exact optimized executable digest.
- Run tests and representative benchmarks with the candidate profile; a default-profile unit test does not exercise the final code-generation policy.
- Bound linker CPU, memory, and wall time in CI. Resource exhaustion is a failed candidate, not a reason to raise limits indefinitely.
- Re-evaluate after compiler, linker, target CPU, or dependency-graph changes.
- Treat an LTO change as a new artifact requiring admission and rollout evidence.

## Cross-Language LTO

Cargo does not natively configure linker-plugin LTO for arbitrary non-Rust inputs. A cross-language setup requires a pinned compatible clang/LLVM/linker toolchain, bitcode-producing native dependencies, explicit build inputs, and target-specific integration tests. Do not paste global workstation `RUSTFLAGS` and assume the C/C++ and Rust toolchains share an LTO format.

## See Also

- [perf-release-profile](./perf-release-profile.md) - make the whole release profile an artifact policy
- [opt-codegen-units](./opt-codegen-units.md) - measure interaction with codegen units
- [opt-pgo-profile](./opt-pgo-profile.md) - use representative runtime profiles
- [perf-profile-first](./perf-profile-first.md) - benchmark before adopting optimization flags
