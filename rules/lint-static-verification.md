# lint-static-verification

> Gate compiler and Clippy lints, formatting, dependency audits, feature combinations, unused dependencies, and unsafe-code checks in CI

## Why It Matters

No single Rust checker covers the production surface. Compiler and Clippy lints catch suspicious code, rustfmt removes style drift, dependency tooling finds vulnerable or unused crates, `cargo hack` exercises Cargo's feature-unification contract, and Miri executes unsafe paths under an aliasing and validity model. Run the relevant checks before merge instead of relying on editor configuration.

## Bad

```yaml
# Only the default feature set is compiled; formatting, advisories,
# unused dependencies, and unsafe behavior are never checked.
- run: cargo test
```

## Good

```yaml
- run: cargo fmt --all --check
- run: cargo clippy --workspace --all-targets --all-features -- -D warnings
- run: cargo audit
- run: cargo hack check --workspace --each-feature
- run: cargo udeps --workspace --all-targets
- run: cargo +nightly miri test --workspace
```

Pin tool versions or toolchains in real CI. Scope Miri to crates and tests that exercise unsafe code when the full workspace is prohibitively slow.

## Workspace Lints

```toml
[workspace.lints.rust]
ambiguous_negative_literals = "warn"
missing_debug_implementations = "warn"
redundant_imports = "warn"
redundant_lifetimes = "warn"
trivial_numeric_casts = "warn"
unsafe_op_in_unsafe_fn = "warn"
unused_lifetimes = "warn"

[workspace.lints.clippy]
cargo = { level = "warn", priority = -1 }
complexity = { level = "warn", priority = -1 }
correctness = { level = "deny", priority = -1 }
pedantic = { level = "warn", priority = -1 }
perf = { level = "warn", priority = -1 }
style = { level = "warn", priority = -1 }
suspicious = { level = "warn", priority = -1 }

allow_attributes_without_reason = "warn"
as_pointer_underscore = "warn"
assertions_on_result_states = "warn"
clone_on_ref_ptr = "warn"
deref_by_slicing = "warn"
disallowed_script_idents = "warn"
empty_drop = "warn"
empty_enum_variants_with_brackets = "warn"
empty_structs_with_brackets = "warn"
fn_to_numeric_cast_any = "warn"
if_then_some_else_none = "warn"
map_err_ignore = "warn"
redundant_type_annotations = "warn"
renamed_function_params = "warn"
semicolon_outside_block = "warn"
undocumented_unsafe_blocks = "warn"
unnecessary_safety_comment = "warn"
unnecessary_safety_doc = "warn"
unneeded_field_pattern = "warn"
unused_result_ok = "warn"

# Structured logging templates intentionally contain braces.
literal_string_with_formatting_args = "allow"
```

Start with the high-signal restriction lints that enforce an adopted rule. Add the rest deliberately, with workspace-level reasons for opt-outs; do not paste a maximal list that the team immediately suppresses.

## Key Points

- Run `cargo hack` across the feature policy you publish, not only `--all-features`.
- Keep `cargo audit` advisory policy explicit and time-bound; never ignore the command because one advisory needs a documented exception.
- Treat `cargo udeps` as a dependency-hygiene signal and account for build-script, target-specific, and generated uses before removal.
- Use `#[expect(..., reason = "...")]` for local lint exceptions so stale suppressions report themselves.
- Keep rustfmt and tool configuration in the repository so local and CI behavior match.

## See Also

- [lint-workspace-lints](lint-workspace-lints.md) - inherit one lint policy across member crates
- [lint-expect-override](lint-expect-override.md) - make local exceptions self-expiring
- [lint-rustfmt-check](lint-rustfmt-check.md) - formatting as a merge gate
- [proj-feature-additive](proj-feature-additive.md) - feature combinations must compose
- [unsafe-miri-ci](unsafe-miri-ci.md) - focused Miri setup and limitations
