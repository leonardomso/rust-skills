# Working on rust-skills

This file is for agents editing this repository. To *use* the Rust rules, read [SKILL.md](SKILL.md) instead.

The repo is a skill: `SKILL.md` is the index agents load, and `rules/<id>.md` holds one rule each. Before adding or editing a rule, read [CONTRIBUTING.md](CONTRIBUTING.md): it has the rule format and the writing conventions.

## Conventions you can't see from the files

- The `## Index` section of `SKILL.md` (to end of file) and the counts and Rust version in `README.md` are generated. Change a rule's `> summary` line or the category config in `checks/gen_index.py`, then run `python3 checks/gen_index.py`.
- The documented Rust version comes from `checks/rust-toolchain.toml`. Bump it there and in `.github/workflows/ci.yml` together, then regenerate `checks/baseline.txt` on the new toolchain.
- Every `rust` block outside a `## Bad` section is compile-checked. Make Good examples self-contained; a block that only references undefined helpers is accepted as a fragment.
- `references/` holds optional companion material that the rules don't depend on.

## Done

`bash checks/check.sh` passes. It runs the same gates as CI: structure and links, index freshness, and the example compile check against `checks/baseline.txt`. If it reports a new compile suspect, fix the example. Refresh the baseline (`checks/README.md`) only for an intentional fragment.
