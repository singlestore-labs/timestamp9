# String to TS 9

```sql
CREATE TABLE `t2` (
  `dt` bigint(20) DEFAULT NULL,
  `str_dt` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `dt6_dt` datetime(6) DEFAULT NULL,
  KEY `__UNORDERED` () USING CLUSTERED COLUMNSTORE
  , SHARD KEY () 
);

set @d = concat(now(6), "999");
insert t2 values 
  (str_to_ts9(@d), @d, SUBSTRING(@d, 1, CHAR_LENGTH(@d) - 3));

set @d = concat(now(6), "555");
insert t2 values 
  (str_to_ts9(@d), @d, SUBSTRING(@d, 1, CHAR_LENGTH(@d) - 3));

/* show functions in SQL select */
select dt, ts9_to_str(dt) as s, str_to_ts9(s), str_dt 
from t2 
order by 1;
```

```sql
singlestore> select * from t2;
+---------------------+-------------------------------+----------------------------+
| dt                  | str_dt                        | dt6_dt                     |
+---------------------+-------------------------------+----------------------------+
| 1679626478941891999 | 2023-03-24 02:54:38.941891999 | 2023-03-24 02:54:38.941891 |
| 1679626478968816555 | 2023-03-24 02:54:38.968816555 | 2023-03-24 02:54:38.968816 |
+---------------------+-------------------------------+----------------------------+

/* notice auto-cast to string for datetime(6) makes it work 
  as argument to str_to_ts9 */

singlestore> select dt, str_to_ts9(dt6_dt) from t2;
+---------------------+---------------------+
| dt                  | str_to_ts9(dt6_dt)  |
+---------------------+---------------------+
| 1679626478941891999 | 1679626478941891000 |
| 1679626478968816555 | 1679626478968816000 |
+---------------------+---------------------+
```