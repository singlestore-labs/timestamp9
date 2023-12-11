-- Create both functions that make up the extension
CREATE FUNCTION ts9_to_str AS WASM FROM LOCAL INFILE "ts9.wasm" WITH WIT FROM LOCAL INFILE "ts9.wit"

CREATE FUNCTION str_to_ts9 AS WASM FROM LOCAL INFILE "ts9.wasm" WITH WIT FROM LOCAL INFILE "ts9.wit"
