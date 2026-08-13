# opt-pgo-profile

> Adopt PGO only with representative profiles, pinned tools, and measured wins

## Why It Matters

Profile-guided optimization feeds observed branch and call frequencies into later compilation. It can improve an application whose production workload is stable and well represented, but stale or biased profiles can regress another tenant, request shape, architecture, or failure path. PGO also adds a training build, workload execution, profile merge, optimized rebuild, and new provenance inputs. Treat it as an artifact pipeline, not a universal performance switch.

## Process

1. **Instrument** the exact source, lockfile, compiler, target, profile, and features intended for the candidate.
2. **Exercise** a versioned, privacy-safe workload representing normal, peak, and important failure paths.
3. **Merge** raw profiles with the `llvm-profdata` shipped for the pinned Rust LLVM toolchain.
4. **Rebuild** from a clean output directory with the merged profile as a declared input.
5. **Compare** against the non-PGO candidate on runtime objectives, size, build cost, and failure behavior.
6. **Promote** only the measured artifact digest together with its profile-data provenance.

## Example

```bash
set -euo pipefail

PGO_ROOT="$PWD/target/pgo"
RAW="$PGO_ROOT/raw"
MERGED="$PGO_ROOT/merged.profdata"

rm -rf "$PGO_ROOT"
mkdir -p "$RAW"

RUSTFLAGS="-Cprofile-generate=$RAW" \
  cargo build --locked --profile release-service --target-dir target/pgo-instrumented

./target/pgo-instrumented/release-service/my_app \
  --replay-manifest tests/pgo/workload-v3.json

rustup run 1.97.1 llvm-profdata merge \
  --failure-mode=all-functions \
  -o "$MERGED" "$RAW"

RUSTFLAGS="-Cprofile-use=$MERGED -Cllvm-args=-pgo-warn-missing-function" \
  cargo build --locked --profile release-service --target-dir target/pgo-optimized
```

The concrete `llvm-profdata` invocation depends on the installed LLVM tools component and target layout. Pin and verify it; do not use an arbitrary system LLVM that may be incompatible with rustc's profile format.

## Representative Workload Contract

- Version and hash the workload manifest and generators.
- Sample production shapes without copying secrets, PII, tenant payloads, or credentials into build inputs.
- Cover dominant normal traffic, large values, error handling, startup, and latency-sensitive minority paths.
- Weight samples from observed distributions; a million repetitions of one tiny operation can distort layout and branch decisions.
- Maintain separate target-architecture profiles when their code generation or workload differs. Do not silently reuse x86 data for Arm.
- Expire profiles after a defined source/feature/toolchain drift threshold and make missing or stale data fail the PGO candidate rather than falling back silently.

## Validation

```bash
hyperfine \
  './target/release-service/my_app --replay-manifest tests/pgo/validation-v3.json' \
  './target/pgo-optimized/release-service/my_app --replay-manifest tests/pgo/validation-v3.json'
```

Use a holdout validation workload that was not the training input. Measure product SLOs, throughput, CPU per operation, artifact size, and tail latency under controlled load. Run correctness and failure-injection tests on the optimized binary. Compiler warnings about missing or mismatched profile data are failed evidence, not noise to suppress.

## BOLT And Other Post-Link Tools

Post-link optimizers are a separate candidate stage with platform, binary-format, unwind, symbol, and sampling requirements. Do not stack BOLT on PGO because an unsourced percentage promises another gain. Pin the tool, retain symbols/unwind information it needs, validate crash symbolization, and compare PGO-only versus PGO-plus-post-link artifacts independently.

## Failure Behavior

- A profile-format mismatch, missing function coverage beyond policy, corrupt data, or stale workload fails the PGO build.
- A candidate that improves average throughput but regresses a protected tail-latency or failure-path objective is rejected.
- A change in toolchain, target features, dependency graph, or important workload distribution triggers retraining and revalidation.
- The profile data, workload identity, compiler identity, and optimized binary digest remain linked for audit and rollback.
- Rollback uses the prior admitted artifact; it does not rebuild from old source with current profile data.

## See Also

- [perf-profile-first](./perf-profile-first.md) - define the performance objective first
- [perf-release-profile](perf-release-profile.md) - keep final profile policy explicit
- [opt-lto-release](./opt-lto-release.md) - measure LTO interaction separately
- [opt-codegen-units](./opt-codegen-units.md) - measure codegen-unit interaction
- [proj-reproducible-runtime](proj-reproducible-runtime.md) - promote exact tested bytes
