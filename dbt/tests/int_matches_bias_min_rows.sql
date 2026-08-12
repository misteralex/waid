-- tests/int_matches_bias_min_rows.sql

with stats as (
    select count(*) as row_count
    from {{ ref('int_matches_bias') }}
)

select *
from stats
where row_count < 100