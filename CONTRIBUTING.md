# Contributing

Thanks for helping improve rust-skills! This repo is a set of focused Rust
best-practice rules consumed by AI coding agents. Contributions usually mean
adding a rule, improving an existing one, or fixing an example.

## Adding or editing a rule

1. **Check for an existing rule first.** Each meaning lives in exactly one rule. Grep `rules/` for the topic; if a rule already covers it, extend that rule instead of adding a second one.

2. **Create `rules/<prefix>-<name>.md`** with a `kebab-case` id that starts with an existing category prefix (the prefixes are listed in `CATEGORIES` in `checks/gen_index.py`; add one there to propose a new category).

3. **Follow the format** exactly:

   ````markdown
   # prefix-rule-name

   > One-line summary that states the target behaviour.

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

   The first line must be `# <id>` matching the filename. `## Why It Matters` and `## See Also` are required, and `See Also` links must point to real rule files.

4. **Write the summary for the index.** The `> summary` line is the only part of a rule an agent sees before deciding to open it. Lead with the action and state what to do ("Accept `&str` and `&[T]` parameters"), not only what to avoid. Name a feature's version when it is new ("stable since Rust 1.100").

5. **Make examples compile on the pinned toolchain** (`checks/rust-toolchain.toml`, edition 2024). Every `rust` block outside `## Bad` is compile-checked, so define the types a Good example uses. Keep error and log strings lowercase with no trailing punctuation.

6. **Regenerate the index** so `SKILL.md` and the README stay in sync. Never hand-edit the generated `## Index` section:

   ```bash
   python3 checks/gen_index.py
   ```

7. **Add a `CHANGELOG.md` entry** under the next version.

## Before opening a PR

```bash
bash checks/check.sh
```

It runs exactly what CI runs: structure, links, index freshness, and the example compile check against `checks/baseline.txt`. If it reports a new compile suspect, fix the example. If you intentionally added a fragment-style snippet, refresh the baseline as described in `checks/README.md`.

## Style

- Be concrete and example-driven.
- Cite sources by name (the Rust Reference, the API Guidelines, a crate) rather than by fragile deep links.
- Keep rules small and single-purpose; cross-link related rules in `See Also`.
