use chrono::NaiveDateTime;

wit_bindgen_rust::export!("ts9.wit");

const BILLION: i64 = 1_000_000_000;

struct Ts9;

impl ts9::Ts9 for Ts9 {
    /// Convert string to number of nanos since midnight on January 1, 1970 as 64-bit int.
    /// Valid range is about 584 years. Max date that can be represented is 2262-04-11.
    /// Numbers must include a fraction but it can be up to 9 digits, and, for example, 
    /// .123 is interpreted as 123000000 ns and .123456789 is interpreted as 123456789 ns.
    fn str_to_ts9(s: String) -> i64 {
        let native_dt = NaiveDateTime::parse_from_str(&s, "%Y-%m-%d %H:%M:%S%.9f").unwrap();
        native_dt.timestamp_nanos()
    }

    /// Convert number of nanos since midnight on January 1, 1970, as 64-bit int,
    /// to string with full 9-digit specification of nanos after the decimal point.
    fn ts9_to_str(dt: i64) -> String {
        // Extract the seconds and nanosecond parts
        let secs = dt / BILLION;
        let nsecs = dt - (secs * BILLION);
        // Convert the nanoseconds to unsigned 32 bit
        assert!(nsecs <= u32::MAX as i64);
        let nsecs = nsecs as u32;
        // Convert to formatted string
        let res = NaiveDateTime::from_timestamp_opt(secs, nsecs).unwrap();
        res.format("%Y-%m-%d %H:%M:%S.%f").to_string()
    }
}

#[cfg(test)]
mod tests {
    // Import the ts9::Ts9 trait so that it's in scope
    use super::ts9::Ts9 as _;
    use super::*;

    const SHORT_CASES: [(&str, i64); 2] = [
        ("2020-03-14 01:59:26.535", 1584151166535000000),
        ("2023-12-11 10:09:08.777", 1702289348777000000),
    ];

    #[test]
    fn test_str_to_ts9() {
        for (str, ts9) in SHORT_CASES.iter() {
            // Test that it produces the expected result
            assert_eq!(Ts9::str_to_ts9(str.to_string()), *ts9);
            // Test that the result is the same with up to 6 trailing zeros
            assert_eq!(Ts9::str_to_ts9(str.to_string() + "0"), *ts9);
            assert_eq!(Ts9::str_to_ts9(str.to_string() + "00"), *ts9);
            assert_eq!(Ts9::str_to_ts9(str.to_string() + "000"), *ts9);
            assert_eq!(Ts9::str_to_ts9(str.to_string() + "0000"), *ts9);
            assert_eq!(Ts9::str_to_ts9(str.to_string() + "00000"), *ts9);
            assert_eq!(Ts9::str_to_ts9(str.to_string() + "000000"), *ts9);
        }
    }

    #[test]
    fn test_ts9_to_str() {
        for (str, ts9) in SHORT_CASES.iter() {
            assert_eq!(Ts9::ts9_to_str(*ts9), str.to_string() + "000000");
        }
    }
}