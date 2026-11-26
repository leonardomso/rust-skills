# name-funcs-snake

> Use `snake_case` for functions, methods, variables, and modules

## Why It Matters

Rust uses `snake_case` for "value-level" names—functions, methods, variables, modules. This convention is enforced by the compiler and distinguishes runtime entities from types. Consistent naming makes code scannable and predictable.

## Bad

```rust
// CamelCase functions - compiler warns
fn calculateTotal() -> f64 { ... }  // warning: function `calculateTotal` should have a snake case name
fn getUserName() -> String { ... }  // warning

// Inconsistent naming
fn get_user() -> User { ... }
fn fetchOrder() -> Order { ... }  // Mixed conventions
```

## Good

```rust
struct Order;
struct User {
    first: String,
    last: String,
    active: bool,
    email: String,
}

// snake_case for functions
fn calculate_total() -> f64 { 0.0 }
fn load_user_name() -> String { String::new() }
fn fetch_order() -> Order { Order }

// snake_case for methods
impl User {
    fn full_name(&self) -> String { format!("{} {}", self.first, self.last) }
    fn is_active(&self) -> bool { self.active }
    fn set_email(&mut self, email: &str) { self.email = email.to_string(); }
}

// snake_case for variables
fn variables() {
    let user_count = 42;
    let max_connections = 100;
    let is_valid = true;
}

// snake_case for modules
mod user_service {}
mod http_client {}
mod json_parser {}
```

## Acronyms in snake_case

```rust
use std::net::TcpStream;

struct Json;
struct Uuid;

// Lowercase acronyms in snake_case
fn parse_json() -> Json { Json }                                  // Not parse_JSON
fn connect_tcp() -> std::io::Result<TcpStream> { TcpStream::connect("127.0.0.1:80") } // Not connect_TCP
fn generate_uuid() -> Uuid { Uuid }                               // Not generate_UUID

fn fetch() -> String { String::new() }

let http_response = fetch();
let json_data = parse_json();
```

## Local Variables

```rust
struct Output;
#[derive(Debug)]
struct Error;

fn decode(raw: &[u8]) -> Result<String, Error> { Ok(String::from_utf8_lossy(raw).into_owned()) }
fn parse(s: &str) -> Result<usize, Error> { Ok(s.len()) }
fn transform(n: usize) -> Result<Output, Error> { let _ = n; Ok(Output) }

fn process_data(input_data: &[u8]) -> Result<Output, Error> {
    let raw_bytes = input_data;
    let decoded_string = decode(raw_bytes)?;
    let parsed_value = parse(&decoded_string)?;
    let final_result = transform(parsed_value)?;
    
    Ok(final_result)
}
```

## See Also

- [name-types-camel](./name-types-camel.md) - Type naming
- [name-consts-screaming](./name-consts-screaming.md) - Constant naming
- [name-lifetime-short](./name-lifetime-short.md) - Lifetime naming
