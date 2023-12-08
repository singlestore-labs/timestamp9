from pathlib import Path
import base64

from singlestoredb.connection import Cursor


CREATE_TABLE_STATEMENT = """
CREATE TABLE `t2` (
  `dt` bigint(20) DEFAULT NULL,
  `str_dt` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `dt6_dt` datetime(6) DEFAULT NULL
)
"""

def test_create_functions(singlestoredb_tempdb: Cursor):
    cursor = singlestoredb_tempdb

    wasm = Path.cwd() / "ts9.wasm"
    wit = Path.cwd() / "ts9.wit"

    wasm_data = base64.b64encode(wasm.read_bytes()).decode()
    wit_data = base64.b64encode(wit.read_bytes()).decode()

    cursor.execute(f"CREATE FUNCTION ts9_to_str AS WASM FROM BASE64 \"{wasm_data}\" WITH WIT FROM BASE64 \"{wit_data}\"")
    cursor.execute(f"CREATE FUNCTION str_to_ts9 AS WASM FROM BASE64 \"{wasm_data}\" WITH WIT FROM BASE64 \"{wit_data}\"")

    cursor.execute(CREATE_TABLE_STATEMENT)
    cursor.execute("set @d = concat(now(6), \"999\")")
    cursor.execute("insert t2 values (str_to_ts9(@d), @d, SUBSTRING(@d, 1, CHAR_LENGTH(@d) - 3));")

    cursor.execute("set @d = concat(now(6), \"555\")")
    cursor.execute("insert t2 values (str_to_ts9(@d), @d, SUBSTRING(@d, 1, CHAR_LENGTH(@d) - 3));")

    cursor.execute("select dt, ts9_to_str(dt) as s, str_to_ts9(s), str_dt from t2 order by 1;")

    results = cursor.fetchall()
    assert len(results) == 2
