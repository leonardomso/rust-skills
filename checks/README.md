# checks — compile-verify the rule examples

A dev tool that type-checks the ` ```rust ` code blocks in `../rules/*.md` so the
"Good" examples we tell agents to write actually compile. Not part of the
published skill.

## Run

```bash
bash checks/check.sh
```

That is the whole CI gate. It runs `validate.py` (structure, links, index parity), `gen_index.py --check`, `gen.py` (extract blocks into `examples/`), `cargo check --examples` on the pinned toolchain and target, and `analyze.py --check-baseline`. To see every suspect with its errors, run `python3 analyze.py check.json` after a run.

## Updating the baseline

`baseline.txt` lists the currently-accepted suspects (fragments/pseudocode the
heuristics can't auto-classify). The CI gate fails only on signatures *not* in
it. After intentionally adding/changing examples, regenerate it on the pinned
toolchain and review the diff:

```bash
bash checks/check.sh   # leaves check.json behind, even when the gate fails
cd checks
python3 analyze.py check.json --emit-baseline > baseline.txt
```

When bumping the pinned toolchain in `ci.yml`, regenerate `baseline.txt` on the
same version in the same commit.

## How it works

Blocks fenced ```` ```rust,compile_fail ```` are checked the other way round: they must fail with a real error (not just an undefined name), so a compile-error demo can't silently start compiling.


`gen.py` extracts each candidate block into `examples/<name>.rs`, wrapping
fragments in an `async fn -> Result<...>` so `?` and `.await` type-check. It
skips blocks that can't compile standalone by design: `## Bad` anti-patterns,
nightly `#![feature]` gates, procedural-macro code, placeholder crate names
(`my_crate`, …), and bare `...` pseudocode.

`analyze.py` buckets each failing example by compiler error code:

- **fragment** — every error is name resolution (undefined symbol/crate). These
  reference helpers defined elsewhere in the rule; expected, ignored.
- **artifact** — caused by extraction (a `&self` method body wrapped as a free
  fn, pseudocode `...`/`???` tokens, dangling doc comments). Not real bugs.
- **low** — only "type annotations needed"; compiles in the rule's real context.
- **SUSPECT** — anything else (type mismatch, no-method, bad syntax, wrong
  arity, missing trait impl). These are the ones to review and fix.

## Notes

- Run on Rust ≥ 1.100: some examples use APIs stabilized in 1.95–1.100 (e.g. the
  `MaybeUninit` array `From` conversions, `core::mem::DropGuard`) and will spuriously fail on older
  toolchains.
- Generated files (`examples/`, `*.json`, `manifest.json`, `target/`) are
  gitignored; only the source (`gen.py`, `analyze.py`, `Cargo.toml`) is tracked.
