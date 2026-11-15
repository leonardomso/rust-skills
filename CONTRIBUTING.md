# Contributing

Thanks for helping improve rust-skills! This repo is a set of focused Rust
best-practice rules consumed by AI coding agents. Contributions usually mean
adding a rule, improving an existing one, or fixing an example.

## Adding or editing a rule

1. **Create `skills/rust/rules/<prefix>-<name>.md`** with a `kebab-case` id that starts with
   an existing category prefix (`own-`, `err-`, `mem-`, `unsafe-`, `api-`,
   `async-`, `conc-`, `opt-`, `num-`, `type-`, `trait-`, `conv-`, `const-`,
   `serde-`, `pat-`, `macro-`, `closure-`, `coll-`, `name-`, `test-`, `doc-`,
   `obs-`, `perf-`, `proj-`, `lint-`, `anti-`). To propose a brand-new category,
   add it to `CATEGORIES` in `skills/rust/checks/gen_index.py`.

2. **Follow the format** of existing rules exactly:

   ````markdown
   # prefix-rule-name

   > One-line imperative summary.

   ## Why It Matters

   Two to four sentences.

   ## Bad

   ```rust
   // the anti-pattern
   ```

   ## Good

   ```rust
   // the recommended pattern
   ```

   ## See Also

   - [other-rule](other-rule.md) - why it's related
   ````

   The first line must be `# <id>` (matching the filename), followed by a `>`
   summary line. `## Why It Matters` and `## See Also` are required; `See Also`
   links must point to real rule files.

3. **Make examples compile on current stable Rust** (2024 edition). Prefer
   self-contained `## Good` examples (define the types you reference) so the
   compile harness can verify them. Keep error/log message strings lowercase
   with no trailing punctuation.

4. **Regenerate the index** so `skills/rust/SKILL.md` and the README counts stay
   in sync — never hand-edit the generated table or Quick Reference:

   ```bash
   python3 skills/rust/checks/gen_index.py
   ```

5. **Add a `CHANGELOG.md` entry** under the next version.

## Before opening a PR

Run the same checks CI runs:

```bash
# structure, links, index parity, and that SKILL.md/README are up to date
python3 skills/rust/checks/validate.py
python3 skills/rust/checks/gen_index.py --check

# compile-check the examples (Rust >= 1.95)
cd skills/rust/checks
python3 gen.py
cargo check --examples --keep-going --message-format=json > check.json
python3 analyze.py check.json --check-baseline baseline.txt
```

If the compile gate reports a real bug, fix the example. If you intentionally
added a new fragment-style snippet, refresh the baseline (see
`skills/rust/checks/README.md`).

## Style

- Be concrete and example-driven, not preachy.
- Cite sources by name (the Rust Reference, the API Guidelines, a crate) rather
  than fragile deep links.
- Keep rules small and single-purpose; cross-link related rules in `See Also`.
