# Rust Skills

![rules](https://img.shields.io/badge/rules-272-blue)
![categories](https://img.shields.io/badge/categories-26-blue)
![Rust](https://img.shields.io/badge/Rust-1.100%20%2F%202024%20edition-orange)
![license](https://img.shields.io/badge/license-MIT-green)

272 Rust rules your AI coding agent can use to write better code. Current for Rust 1.100 (2024 edition).

Works with Claude Code, Cursor, Windsurf, Copilot, Codex, Aider, Zed, Amp, Cline, and pretty much any other agent that supports skills.

## Why

Out of the box, coding agents write *average* Rust — they clone to dodge the borrow checker, `.unwrap()` everything, and reach for `Box<dyn Trait>` when `impl Trait` would do. These rules encode what expert Rust actually looks like: idiomatic, fast, and safe. Each rule is small and focused, so the agent pulls in only what's relevant to the code in front of it.

## Install

```bash
npx skills add leonardomso/rust-skills
```

That's it. The [`skills`](https://github.com/vercel-labs/skills) CLI figures out which agents you have and installs the skill to the right place.

**Requirements:** a recent Node.js. The `skills` CLI declares `node >= 22.20.0`; older releases such as Node 18 (the default on Ubuntu 24.04) fail with:

```
SyntaxError: The requested module 'node:util' does not provide an export named 'styleText'
```

Upgrade Node (for example with [nvm](https://github.com/nvm-sh/nvm): `nvm install --lts`), or skip the CLI and use one of the [manual installs](#manual-install) below. They only need `git` or `curl`. The old `npx add-skill` command is deprecated; use `npx skills add` instead.

## How to use it

After installing, just ask your agent:

```
/rust-skills review this function
```

```
/rust-skills is my error handling idiomatic?
```

```
/rust-skills check for memory issues
```

```
/rust-skills is this unsafe block sound?
```

The agent loads the relevant rules and applies them to your code.

## See it in action

Ask the agent to review a function like this:

```rust
// before
fn first_word(s: &String) -> String {
    s.clone().split_whitespace().next().unwrap().to_string()
}
```

With these rules loaded, it knows to take `&str` instead of `&String`, drop the
needless `clone()` and allocation, and return an `Option` instead of panicking:

```rust
// after — applies own-slice-over-vec, own-borrow-over-clone, err-no-unwrap-prod
fn first_word(s: &str) -> Option<&str> {
    s.split_whitespace().next()
}
```

## What's in here

272 rules split into 26 categories:

| Category | Rules | What it covers |
|----------|-------|----------------|
| **Ownership & Borrowing** | 12 | When to borrow vs clone, Arc/Rc, lifetimes |
| **Error Handling** | 11 | thiserror for libs, anyhow for apps, the `?` operator |
| **Memory** | 20 | SmallVec, arenas, avoiding allocations, `mem::take`, drop order |
| **Unsafe Code** | 8 | `SAFETY:` comments, Miri, `MaybeUninit`, 2024-edition unsafe |
| **API Design** | 23 | Builder pattern, newtypes, sealed traits, `FromIterator` |
| **Async** | 20 | Tokio patterns, channels, async fn in traits, cancel safety |
| **Concurrency** | 4 | rayon, scoped threads, atomic ordering, thread-locals |
| **Optimization** | 11 | LTO, inlining, PGO, SIMD |
| **Numeric & Arithmetic** | 5 | Overflow handling, `as` vs `TryFrom`, float compare, `NonZero` |
| **Type Safety** | 13 | Newtypes, parse don't validate, `Deref`, `Display`/`Debug` |
| **Trait & Generics Design** | 6 | dyn vs generic, associated types, blanket impls, object safety, orphan rule |
| **Conversions** | 3 | `TryFrom`, `FromStr`, `AsMut` |
| **Const & Compile-Time** | 4 | `const fn`, const vs static, const generics, `const {}` blocks |
| **Serde** | 8 | rename_all, default, flatten, enum tagging, validate-on-deserialize |
| **Pattern Matching** | 5 | `let-else`, `matches!`, if-let chains, exhaustive matches |
| **Macros** | 10 | `macro_rules!` hygiene, fragment specifiers, proc-macros with syn/quote |
| **Closures** | 5 | Fn/FnMut/FnOnce bounds, returning `impl Fn`, move & disjoint capture |
| **Collections** | 4 | HashMap/BTreeMap/IndexMap, Vec/VecDeque, sets, `BinaryHeap` |
| **Naming** | 16 | Following Rust API Guidelines |
| **Testing** | 17 | Proptest, mockall, criterion, loom, snapshot tests |
| **Docs** | 13 | Doc examples, intra-doc links, README/crate-doc unification |
| **Observability** | 8 | tracing over log, spans, structured fields, redacting secrets |
| **Performance** | 13 | Iterators, entry API, faster hashers, I/O buffering |
| **Project Structure** | 15 | Workspaces, module layout, features, MSRV |
| **Linting** | 16 | Clippy config, CI setup, `unexpected_cfgs` |
| **Anti-patterns** | 2 | Common mistakes, each mapped to the rule that fixes it |

Each rule has:
- Why it matters
- A bad code example
- A good code example
- Links to related rules and sources

## How it works

The design is built for low token cost and easy auditing:

- **[`SKILL.md`](./SKILL.md)** is a lightweight index — every rule listed as a one-line summary, grouped by category, with a link to its file. The agent reads this first.
- **[`rules/`](./rules)** holds one Markdown file per rule (`<prefix>-<name>.md`). The agent opens only the handful relevant to your code instead of loading every rule. Progressive disclosure keeps context small.
- **Prefixes** (`own-`, `err-`, `unsafe-`, `async-`, …) map directly to categories, so an agent reviewing async code can pull just `async-`, `conc-`, and `own-` rules.

- **Anti-patterns** is a lookup: each common mistake points at the rule that fixes it, so a reviewer can start from the symptom.

`AGENTS.md` (and its `CLAUDE.md` symlink) is for agents *editing this repo*, not for using the rules.

## Manual install

If `npx skills add` doesn't work for your setup (no Node, an old Node, or a locked-down machine), install manually. The `git clone` options give the agent every rule file. The `curl` options copy only the index (`SKILL.md`); the agent then fetches individual rules from GitHub when it needs them.

<details>
<summary><b>Claude Code</b></summary>

Global (applies to all projects):
```bash
git clone https://github.com/leonardomso/rust-skills.git ~/.claude/skills/rust-skills
```

Or just for one project:
```bash
git clone https://github.com/leonardomso/rust-skills.git .claude/skills/rust-skills
```
</details>

<details>
<summary><b>OpenCode</b></summary>

```bash
git clone https://github.com/leonardomso/rust-skills.git .opencode/skills/rust-skills
```
</details>

<details>
<summary><b>Cursor</b></summary>

```bash
git clone https://github.com/leonardomso/rust-skills.git .cursor/skills/rust-skills
```

Or just grab the skill file:
```bash
curl -o .cursorrules https://raw.githubusercontent.com/leonardomso/rust-skills/master/SKILL.md
```
</details>

<details>
<summary><b>Windsurf</b></summary>

```bash
mkdir -p .windsurf/rules
curl -o .windsurf/rules/rust-skills.md https://raw.githubusercontent.com/leonardomso/rust-skills/master/SKILL.md
```
</details>

<details>
<summary><b>OpenAI Codex</b></summary>

```bash
git clone https://github.com/leonardomso/rust-skills.git .codex/skills/rust-skills
```

Or use the AGENTS.md standard:
```bash
curl -o AGENTS.md https://raw.githubusercontent.com/leonardomso/rust-skills/master/SKILL.md
```
</details>

<details>
<summary><b>GitHub Copilot</b></summary>

```bash
mkdir -p .github
curl -o .github/copilot-instructions.md https://raw.githubusercontent.com/leonardomso/rust-skills/master/SKILL.md
```
</details>

<details>
<summary><b>Aider</b></summary>

Add to `.aider.conf.yml`:
```yaml
read: path/to/rust-skills/SKILL.md
```

Or pass it directly:
```bash
aider --read path/to/rust-skills/SKILL.md
```
</details>

<details>
<summary><b>Zed</b></summary>

```bash
curl -o AGENTS.md https://raw.githubusercontent.com/leonardomso/rust-skills/master/SKILL.md
```
</details>

<details>
<summary><b>Amp</b></summary>

```bash
git clone https://github.com/leonardomso/rust-skills.git .agents/skills/rust-skills
```
</details>

<details>
<summary><b>Cline / Roo Code</b></summary>

```bash
mkdir -p .clinerules
curl -o .clinerules/rust-skills.md https://raw.githubusercontent.com/leonardomso/rust-skills/master/SKILL.md
```
</details>

<details>
<summary><b>Other agents (AGENTS.md)</b></summary>

If your agent supports the [AGENTS.md](https://agents.md) standard:
```bash
curl -o AGENTS.md https://raw.githubusercontent.com/leonardomso/rust-skills/master/SKILL.md
```
</details>

## All rules

See [SKILL.md](./SKILL.md) for the full list with links to each rule file.

## Where the rules come from

The rules are not copied from any single source. Each one is an original write-up that distills guidance from the official Rust documentation, the Rust API Guidelines, well-known books, and idioms seen in widely used crates (listed below). Two things keep them honest:

- **Compile-checked examples.** Every `rust` block outside a `## Bad` section is extracted and type-checked in CI on a pinned toolchain (currently Rust 1.100.0) by the harness in [`checks/`](./checks). Run it locally with `bash checks/check.sh`.
- **Public review.** Several rules have been corrected after readers reported problems, sometimes with reproductions or benchmarks. If you think a rule is wrong, open an issue with a minimal example.

## Sources & attribution

These rules are an independent synthesis of official Rust guidance, well-known books, and patterns drawn from widely-used open-source crates. They are not affiliated with or endorsed by the Rust project or any crate author. The text and code examples are original summaries — no substantial content is copied from the sources below.

**Official Rust documentation**
- [The Rust Reference](https://doc.rust-lang.org/reference/)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- [The Rustonomicon](https://doc.rust-lang.org/nomicon/) (unsafe code)
- [Rust 2024 Edition Guide](https://doc.rust-lang.org/edition-guide/rust-2024/)
- [The Cargo Book](https://doc.rust-lang.org/cargo/)
- [Standard library docs](https://doc.rust-lang.org/std/) and [release notes](https://doc.rust-lang.org/releases.html)

**Books & guides**
- [The Rust Performance Book](https://nnethercote.github.io/perf-book/) — Nicholas Nethercote
- [Rust Design Patterns](https://rust-unofficial.github.io/patterns/) — rust-unofficial
- [Rust Atomics and Locks](https://marabos.nl/atomics/) — Mara Bos
- [Effective Rust](https://effective-rust.com/) — David Drysdale

**Companion guidelines**
- [Microsoft Pragmatic Rust Guidelines](https://microsoft.github.io/rust-guidelines/) (MIT). Widely accepted items were adopted as new rules, written in this repo's own words, and each credits its source guideline. [`references/pragmatic-rust-guidelines.md`](./references/pragmatic-rust-guidelines.md) maps every `M-*` guideline to our rules and explains what was left out. It is optional reading for teams that want the full Microsoft style.

**Tooling**
- [Clippy lint documentation](https://rust-lang.github.io/rust-clippy/)
- [Miri](https://github.com/rust-lang/miri)

**Real-world codebases studied for idioms**
- ripgrep, tokio, serde, clap, polars, axum, cargo, hyper, bevy, rayon, and dtolnay's crates (thiserror, anyhow, syn)

This project is MIT-licensed. Referenced upstream materials remain under their own licenses — the official Rust documentation and API Guidelines are dual [MIT](https://github.com/rust-lang/rust/blob/master/LICENSE-MIT) / [Apache-2.0](https://github.com/rust-lang/rust/blob/master/LICENSE-APACHE).

## Contributing

PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the rule format and the one command to run before opening a PR (`bash checks/check.sh`).

## License

MIT
