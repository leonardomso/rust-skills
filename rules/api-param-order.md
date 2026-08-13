# api-param-order

> Keep the same conceptual parameters in the same order across related functions

## Why It Matters

When `member_id` and `org_id` swap places between `add` and `drop`, a caller who copies an earlier call site silently transposes arguments of the same type. put call-specific values first, shared context (loggers, clocks) last, and a single closure last of all. One order, used everywhere in the crate, is cheaper to review than a comment on each function.

## Bad

```rust
pub struct Logger;
pub struct OrgId(pub u64);
pub struct MemberId(pub u64);

pub fn add_member(logger: &Logger, member_id: MemberId, org_id: OrgId) -> bool {
    let _ = (logger, member_id, org_id);
    true
}

pub fn drop_member(org_id: OrgId, member_id: MemberId, logger: &Logger) -> bool {
    let _ = (logger, member_id, org_id);
    true
}
```

## Good

```rust
pub struct Logger;
pub struct OrgId(pub u64);
pub struct MemberId(pub u64);

pub fn add_member(org_id: OrgId, member_id: MemberId, logger: &Logger) -> bool {
    let _ = (logger, member_id, org_id);
    true
}

pub fn drop_member(org_id: OrgId, member_id: MemberId, logger: &Logger) -> bool {
    let _ = (logger, member_id, org_id);
    true
}

pub fn rename_member(
    org_id: OrgId,
    member_id: MemberId,
    new_name: &str,
    logger: &Logger,
) -> bool {
    let _ = (logger, member_id, org_id, new_name);
    true
}

fn main() {
    let logger = Logger;
    let _ = add_member(OrgId(1), MemberId(2), &logger);
    let _ = drop_member(OrgId(1), MemberId(2), &logger);
    let _ = rename_member(OrgId(1), MemberId(2), "ada", &logger);
}
```

## See Also

- [api-newtype-safety](api-newtype-safety.md) - newtypes catch swaps that parameter order alone cannot
- [name-funcs-snake](name-funcs-snake.md) - consistent names make a consistent order easier to scan
- [doc-all-public](doc-all-public.md) - document the shared order once at the module, not on every signature
