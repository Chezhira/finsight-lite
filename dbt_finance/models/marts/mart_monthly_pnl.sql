with pnl as (
    select
        period,
        entity,
        sum(case when pnl_group = 'Revenue' then signed_amount_kes else 0 end) as revenue,
        sum(case when pnl_group = 'COGS' then signed_amount_kes else 0 end) as cogs,
        sum(case when pnl_group = 'Opex' then signed_amount_kes else 0 end) as opex
    from {{ ref('stg_gl_transactions') }}
    where is_pnl_account
    group by 1, 2
)
select
    period,
    entity,
    revenue,
    cogs,
    revenue - cogs as gross_profit,
    case when revenue = 0 then null else (revenue - cogs) / revenue end as gross_margin_percent,
    opex,
    revenue - cogs - opex as operating_profit_proxy
from pnl
