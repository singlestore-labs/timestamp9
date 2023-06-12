wit_bindgen_rust::export!("ts9.wit");
struct Ts9;
use chrono::NaiveDateTime;

impl ts9::Ts9 for Ts9 {

    // Convert string to number of nanos since midnight on January 1, 1970 as 64-bit int.
    // Valid range is about 584 years. Max date that can be represented is 2262-04-11.
    // Numbers must include a fraction but it can be up to 9 digits, and, for example, 
    // .123 is interpreted as 123000000 ns and .123456789 is interpreted as 123456789 ns.

    fn str_to_ts9(s: String) -> i64 {
        let parse_res = NaiveDateTime::parse_from_str(&s, "%Y-%m-%d %H:%M:%S%.9f");

        let dt = parse_res.unwrap();
        let ns = dt.timestamp_nanos();
        ns
    }

    // Convert number of nanos since midnight on January 1, 1970, as 64-bit int,
    // to string with full 9-digit specification of nanos after the decimal point.
    
    fn ts9_to_str(dt: i64) -> String {
        let billion = 1000000000;
        let dt_sec = dt/billion;
        let ns = (dt - (dt_sec * billion)) as u32;
        let res_ndt = NaiveDateTime::from_timestamp_opt(dt_sec, ns).unwrap();
        let res = res_ndt.format("%Y-%m-%d %H:%M:%S.%f").to_string();
        res
    }
}
