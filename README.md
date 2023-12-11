# Timestamp 9

A SingleStore extension using the Abstract Data Type (ADT) pattern.

## Usage

The Wasm functions can be individually.

```
CREATE FUNCTION ts9_to_str AS WASM FROM LOCAL INFILE "ts9.wasm" WITH WIT FROM LOCAL INFILE "ts9.wit"

CREATE FUNCTION str_to_ts9 AS WASM FROM LOCAL INFILE "ts9.wasm" WITH WIT FROM LOCAL INFILE "ts9.wit"
```

For more examples, checkout the [db tests](./db-tests/test_create_function.py).

### Post 8.5

After release 8.5, you'll be able to install it as an extension.

```sql
CREATE EXTENSION ts9 FROM ...
```

## Building

In order to build the Wasm

1. Install Rust and Cargo
2. Install the Rust `wasm32-wasi` target
3. Run `cargo build --target wasm32-wasi`

## Testing

There are automated script tests in the `db-tests` directory.
They are run against the `singlestoredb-dev-image`.

In order to run the tests

1. Install Python 3
2. Install `singlestoredb` and `pytest` (and optionally `pytest-xdist`)
3. Set the `SINGLESTORE_LICENSE` environment variable
4. Run the `pytest` command

If you installed `pytest-xdist`, you can also distribute the tests to multiple workers
by running `pytest -n auto` or giving a specific number instead of `auto`
