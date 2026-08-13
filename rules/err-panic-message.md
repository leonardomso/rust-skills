# err-panic-message

> Give every intentional production panic a message that identifies the violated contract and relevant values

## Why It Matters

A bare `assert!`, `panic!`, `unreachable!`, or `todo!` terminates work without telling an operator what invariant failed. Intentional panics represent bugs or contract violations; their messages are often the only evidence available before a process restarts. State the expected condition and include safe values that make the defect reproducible.

Messages for caller misuse should explain how to correct the call. Messages for internal bugs should help the maintainer locate the broken invariant. Tests may omit a custom message when the assertion expression and test name already provide the required context.

## Bad

```rust
pub fn frame_payload(frame: &[u8], header_len: usize) -> &[u8] {
    assert!(frame.len() >= header_len);
    &frame[header_len..]
}

pub fn state_name(code: u8) -> &'static str {
    match code {
        0 => "idle",
        1 => "running",
        _ => unreachable!(),
    }
}
```

## Good

```rust
pub fn frame_payload(frame: &[u8], header_len: usize) -> &[u8] {
    assert!(
        frame.len() >= header_len,
        "frame shorter than declared header: frame={} header={header_len}",
        frame.len(),
    );
    &frame[header_len..]
}

pub fn state_name(code: u8) -> &'static str {
    match code {
        0 => "idle",
        1 => "running",
        _ => unreachable!("validated state code escaped decoder: {code}"),
    }
}

fn main() {
    assert_eq!(frame_payload(b"headbody", 4), b"body");
    assert_eq!(state_name(1), "running");
}
```

## Key Points

- Include the violated invariant, not a generic `"failed"` or `"impossible"`.
- Include identifiers, lengths, states, or bounds needed to diagnose the bug, but never secrets or PII.
- Use `expect` text to explain why success was guaranteed at that point.
- A useful message does not make an expected failure panic-worthy; return `Result` for recoverable conditions.

## See Also

- [err-expect-bugs-only](err-expect-bugs-only.md) - reserve `expect` for proven invariants
- [err-result-over-panic](err-result-over-panic.md) - distinguish recovery from contract violations
- [obs-no-sensitive-data](obs-no-sensitive-data.md) - panic diagnostics must not leak secrets
- [doc-panics-section](doc-panics-section.md) - document when a public function can panic
