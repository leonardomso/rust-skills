#!/usr/bin/env bash
# One command that reproduces CI locally. Run from anywhere:
#
#     bash checks/check.sh
#
# It runs the exact same gates CI runs, pinned to the same toolchain
# (checks/rust-toolchain.toml -> Rust 1.97.1) and the same compile target
# (x86_64-unknown-linux-gnu), so a green run here means a green run on CI.
# On non-x86 hosts (e.g. Apple Silicon) the examples are cross-checked for that
# target — `cargo check` type-checks without linking, so no cross-linker needed.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="x86_64-unknown-linux-gnu"
MICROSOFT_COMMIT="bbf7b03f3a51548f187888fb8c516e8118ebb1c2"
MICROSOFT_RUST_GUIDELINES_ROOT="${MICROSOFT_RUST_GUIDELINES_ROOT:-$ROOT/checks/target/microsoft-rust-guidelines-$MICROSOFT_COMMIT}"

if [[ ! -d "$MICROSOFT_RUST_GUIDELINES_ROOT/.git" ]]; then
    git clone --filter=blob:none https://github.com/microsoft/rust-guidelines.git \
        "$MICROSOFT_RUST_GUIDELINES_ROOT"
fi
git -C "$MICROSOFT_RUST_GUIDELINES_ROOT" fetch --depth 1 origin "$MICROSOFT_COMMIT"
git -C "$MICROSOFT_RUST_GUIDELINES_ROOT" checkout --detach "$MICROSOFT_COMMIT"
export MICROSOFT_RUST_GUIDELINES_ROOT

echo "==> structure, links, and index parity"
python3 "$ROOT/checks/validate.py"
python3 "$ROOT/checks/gen_index.py" --check

echo "==> source-guidance behavior checks"
cd "$ROOT/checks"
cargo test --test source_guidance

echo "==> Rust 1.95-1.97 behavior checks"
cargo test --test release_195_197

echo "==> generating example files from rules"
python3 gen.py

echo "==> compile-checking examples (target: $TARGET)"
# cargo exits non-zero on the intentional fragment snippets; the baseline gate
# below is what decides pass/fail.
cargo check --examples --target "$TARGET" --keep-going --message-format=json \
    > check.json 2> check.err || true

echo "==> gating against the baseline"
python3 analyze.py check.json --check-baseline baseline.txt

echo "All checks passed."
