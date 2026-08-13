use std::cmp::Ordering;
use std::collections::{BTreeMap, LinkedList, VecDeque};
use std::num::NonZeroU8;
use std::sync::atomic::{AtomicU64, Ordering as AtomicOrdering};

enum Command {
    SetPort(String),
    Stop,
}

fn parse_port(command: Command) -> Option<u16> {
    match command {
        Command::SetPort(raw)
            if let Ok(port) = raw.parse::<u16>()
                && port != 0 =>
        {
            Some(port)
        }
        Command::SetPort(_) | Command::Stop => None,
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
struct JobKey {
    priority: u8,
    id: u64,
}

#[test]
fn if_let_guard_binds_only_valid_port() {
    assert_eq!(parse_port(Command::SetPort("8080".to_owned())), Some(8080));
    assert_eq!(parse_port(Command::SetPort("0".to_owned())), None);
    assert_eq!(parse_port(Command::SetPort("invalid".to_owned())), None);
    assert_eq!(parse_port(Command::Stop), None);
}

#[test]
fn atomic_update_and_try_update_preserve_contracts() {
    let counter = AtomicU64::new(4);
    assert_eq!(
        counter.update(
            AtomicOrdering::Relaxed,
            AtomicOrdering::Relaxed,
            |current| current + 1
        ),
        4,
    );
    assert_eq!(counter.load(AtomicOrdering::Relaxed), 5);

    assert_eq!(
        counter.try_update(
            AtomicOrdering::Relaxed,
            AtomicOrdering::Relaxed,
            |current| { (current < 6).then_some(current + 1) }
        ),
        Ok(5),
    );
    assert_eq!(
        counter.try_update(
            AtomicOrdering::Relaxed,
            AtomicOrdering::Relaxed,
            |current| { (current < 6).then_some(current + 1) }
        ),
        Err(6),
    );
}

#[test]
fn cfg_select_chooses_exactly_one_branch() {
    let precedence = cfg_select! {
        any(unix, windows) => "first",
        unix => "second",
        _ => "fallback",
    };
    assert_eq!(precedence, "first");

    let pointer_bits = cfg_select! {
        target_pointer_width = "64" => 64,
        target_pointer_width = "32" => 32,
        _ => 0,
    };
    assert_eq!(pointer_bits, usize::BITS);
}

#[test]
fn derived_order_is_total_and_keeps_distinct_keys() {
    let low = JobKey {
        priority: 1,
        id: 10,
    };
    let high_a = JobKey {
        priority: 2,
        id: 20,
    };
    let high_b = JobKey {
        priority: 2,
        id: 21,
    };

    assert_eq!(low.cmp(&low), Ordering::Equal);
    assert_eq!(high_a.cmp(&high_b) == Ordering::Equal, high_a == high_b);
    assert!(low < high_a && high_a < high_b && low < high_b);

    let mut left = BTreeMap::from([(high_a, "a")]);
    let mut right = BTreeMap::from([(high_b, "b")]);
    left.append(&mut right);
    assert_eq!(left.len(), 2);
    assert!(right.is_empty());
}

#[test]
fn fallible_bool_and_nonzero_ranges_reject_invalid_states() {
    assert_eq!(bool::try_from(0_u8), Ok(false));
    assert_eq!(bool::try_from(1_u8), Ok(true));
    assert!(bool::try_from(2_u8).is_err());

    let start = NonZeroU8::new(1).expect("one is non-zero");
    let end = NonZeroU8::new(4).expect("four is non-zero");
    let values: Vec<u8> = (start..end).map(NonZeroU8::get).collect();
    assert_eq!(values, [1, 2, 3]);
}

#[test]
fn integer_bit_helpers_define_zero_and_set_bit_behavior() {
    assert_eq!(0_u32.bit_width(), 0);
    assert_eq!(0b1110_u32.bit_width(), 4);
    assert_eq!(0_u32.highest_one(), None);
    assert_eq!(0b1_0100_u32.highest_one(), Some(4));
    assert_eq!(0b1_0100_u32.lowest_one(), Some(2));
    assert_eq!(0b1_0100_u32.isolate_highest_one(), 0b1_0000);
    assert_eq!(0b1_0100_u32.isolate_lowest_one(), 0b100);
}

#[test]
fn mutable_insert_returns_the_inserted_value() {
    let mut values = Vec::new();
    let inserted = values.push_mut(String::from("request"));
    inserted.push_str("-ready");
    assert_eq!(values, ["request-ready"]);

    let inserted = values.insert_mut(0, String::from("first"));
    inserted.push_str("-ready");
    assert_eq!(values, ["first-ready", "request-ready"]);

    let mut deque = VecDeque::new();
    deque.push_back_mut(String::from("back")).push_str("-ready");
    deque
        .push_front_mut(String::from("front"))
        .push_str("-ready");
    deque
        .insert_mut(1, String::from("middle"))
        .push_str("-ready");
    assert_eq!(deque, ["front-ready", "middle-ready", "back-ready"]);

    let mut list = LinkedList::new();
    list.push_back_mut(String::from("back")).push_str("-ready");
    list.push_front_mut(String::from("front"))
        .push_str("-ready");
    assert_eq!(
        list.into_iter().collect::<Vec<_>>(),
        ["front-ready", "back-ready"]
    );
}
