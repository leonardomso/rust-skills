# Changelog

All notable changes to this skill are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and the project aims to follow
semantic versioning for the rule set.

## [1.7.0]

Documentation pass for agents. Now 272 rules across 26 categories.

### Changed
- **Merged 17 duplicate rules** into the rule that already owned each meaning,
  folding in their unique examples and caveats. Removed ids and their new home:
  `anti-unwrap-abuse` → `err-no-unwrap-prod`, `anti-expect-lazy` →
  `err-expect-bugs-only`, `anti-panic-expected` → `err-result-over-panic`,
  `err-doc-errors` → `doc-errors-section`, `anti-clone-excessive` →
  `own-borrow-over-clone`, `anti-string-for-str` and `anti-vec-for-slice` →
  `own-slice-over-vec`, `anti-lock-across-await` → `async-no-lock-await`,
  `anti-index-over-iter` → `perf-iter-over-index`, `anti-collect-intermediate`
  → `perf-collect-once`, `anti-format-hot-path` → `mem-write-over-format`,
  `anti-premature-optimize` → `perf-profile-first`, `anti-stringly-typed` →
  `type-no-stringly`, `anti-type-erasure` → `trait-dyn-vs-generic`,
  `name-iter-convention` → `name-iter-method`, `doc-link-types` →
  `doc-intra-links`, `opt-cold-unlikely` → `opt-inline-never-cold`.
- The Anti-patterns section of the index is now a symptom → rule lookup
  (generated from `ANTI_LOOKUP` in `checks/gen_index.py`).
- `SKILL.md` restructured: the how-to-use steps and the task → categories
  table come first, with a done condition, and the generated index runs to the
  end of the file. Removed sections that repeated the description, the index,
  or other rules ("When to Apply", the priority table, recommended Cargo
  settings, attribution). The skill description now lists trigger cases
  instead of categories.
- Rule summaries state the target behaviour instead of a prohibition.
- `AGENTS.md` / `CLAUDE.md` are now a short guide for agents editing this
  repo, instead of symlinks that loaded the whole rule index.
- `CONTRIBUTING.md` gained "check for an existing rule first" and summary
  guidance; it and `checks/README.md` point at `bash checks/check.sh` instead
  of repeating its commands.
- README: single-file (`curl`) installs fetch rules from GitHub on demand.
  The contributing section points at `CONTRIBUTING.md`.

## [1.6.0]

Current for Rust 1.100. Now 289 rules across 26 categories.

### Added
- 18 rules adopted from Microsoft's Pragmatic Rust Guidelines, written in
  this repo's own words: `api-types-send`, `api-dont-leak-types`,
  `api-impl-rangebounds`, `api-sans-io`, `api-no-glob-reexports`,
  `api-avoid-statics`, `async-yield-points`, `async-future-size`,
  `unsafe-sound-abstractions`, `mem-shrink-to-fit`, `mem-global-allocator`,
  `test-no-tautological`, `test-utils-feature-gated`, `name-weasel-words`,
  `obs-log-overhead`, `doc-first-sentence`, `lint-expect-over-allow`,
  `macro-pin-impl-crate` (#3).
- `references/pragmatic-rust-guidelines.md`: an optional crosswalk from every
  `M-*` guideline to these rules, including what was not adopted and why.
- Rules for features stabilized in Rust 1.95–1.100: `mem-allocator-api`,
  `macro-cfg-select`, `lint-cargo-lints`, `lint-build-warnings`,
  `proj-dependency-cooldown`, `doc-alias-suggestions`.
- A "Where the rules come from" section in the README (#1).

### Changed
- Every category reviewed against Rust 1.100. Highlights: never type and
  `Infallible = !`, `std::mem::DropGuard`, `NumBuffer::format_into`, atomic
  `update`/`try_update`, `LocalKey::update`, `if let` guards,
  `assert_matches!`, sample-based PGO, `[lints.cargo]`, `build.warnings`,
  the `debug` profile, and clippy lint groups re-verified on 1.100.
- `async-clone-before-await` rewritten: clone the `Arc` handle, not its
  contents; cloning an `Rc` never makes a future `Send` (#10).
- `async-fn-in-trait`: `trait-variant` does not make a trait
  dyn-compatible; added a compile-checked boxed-future adapter (#6).
- Ownership rules corrected and clarified: `&Path` vs strings, `Mutex`
  sizes, `RwLock` downgrade, `Cow::to_mut` vs `into_owned`, and more (#8).
- Install instructions now use `npx skills add` and document the Node.js
  >= 22.20 requirement and a Node-free fallback (#9).
- The compile harness is pinned to Rust 1.100.0, and the example
  dependencies are on current majors (syn 3, mockall 0.15, parking_lot 0.13).
  Fixing broken Good examples cut the accepted-suspect baseline from 123
  to 96.
- `checks/gen_index.py` also keeps the README category counts and the
  documented Rust version (read from `checks/rust-toolchain.toml`) in sync.

## [1.5.1]

### Changed
- Depth pass: expanded `own-rc-single-thread` (breaking cycles with `Weak`, the
  `Rc::clone` idiom, `strong_count`/`weak_count`, `!Send`/`!Sync`) and
  `own-refcell-interior` (`Cell` for `Copy` types).
- Added cross-references from ~18 foundational rules to the newer categories
  (`conc-`, `conv-`, `num-`, `serde-`, `trait-`, `closure-`, `coll-`, `pat-`)
  for better navigation between related rules.

## [1.5.0]

### Added
- **Const & Compile-Time** category (`const-`, 4 rules): `const fn`, `const` vs
  `static`, const generics, inline `const { }` blocks.
- **Trait & Generics Design** category (`trait-`, 6 rules): static vs dynamic
  dispatch, associated types vs generic params, default methods, blanket impls,
  object safety, the orphan rule + newtype.
- **Collections** category (`coll-`, 4 rules): map choice (HashMap/BTreeMap/
  IndexMap), sequence choice (Vec/VecDeque), set membership, `BinaryHeap`.
- `checks/gen_index.py` — generates `SKILL.md`'s priority table and Quick
  Reference (and the rule counts) from `rules/` so the index can't drift; CI
  runs it in `--check` mode.
- `CONTRIBUTING.md` and this `CHANGELOG.md`.

Now 265 rules across 26 categories.

## [1.4.0]

### Added
- **Closures** category (`closure-`, 5 rules): Fn/FnMut/FnOnce bounds, returning
  `impl Fn`, `move` capture, static vs dynamic dispatch, disjoint capture.

Now 251 rules across 23 categories.

## [1.3.0]

### Added
- **Serde** category (`serde-`, 8 rules): rename_all, default, skip, flatten,
  enum representation, deny_unknown_fields, custom (de)serialize, validate-on-
  deserialize.
- **Numeric & Arithmetic Safety** category (`num-`, 5 rules): explicit overflow
  handling, `as` vs `TryFrom`, float comparison, clamping, `NonZero`.

Now 246 rules across 22 categories.

## [1.2.0]

### Added
- **Macros** category (`macro-`, 8 rules): declarative-macro hygiene and
  fragment specifiers, and procedural-macro design with `syn`/`quote`.
- **Observability** category (`obs-`, 7 rules): `tracing`, spans, structured
  fields, error chains, and keeping secrets out of logs.

Now 233 rules across 20 categories.

## [1.1.x]

### Added
- **Unsafe Code** (`unsafe-`), **Concurrency** (`conc-`), **Conversions**
  (`conv-`), and **Pattern Matching** (`pat-`) categories, plus new rules across
  existing categories — 39 rules in total.
- A compile-check harness (`checks/`) and a GitHub Actions CI workflow that
  validates rule structure, links, the index, and that examples compile.

### Changed
- Updated throughout for the Rust 2024 edition and current stable (Rust 1.96):
  fixed `&mut T` is not `Copy`, `impl Trait` in traits, `collect_into` status,
  `resolver = "3"`, `env::set_var` now `unsafe`, and more.

Now 218 rules across 18 categories.

## [1.0.0]

### Added
- Initial release: 179 rules across 14 categories.

[1.5.0]: https://github.com/leonardomso/rust-skills
[1.4.0]: https://github.com/leonardomso/rust-skills
[1.3.0]: https://github.com/leonardomso/rust-skills
[1.2.0]: https://github.com/leonardomso/rust-skills
[1.1.x]: https://github.com/leonardomso/rust-skills
[1.0.0]: https://github.com/leonardomso/rust-skills
