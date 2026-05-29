with actuals as (
    select period, entity, 'Revenue' as category, revenue as actual_amount from {{ ref('mart_monthly_pnl') }}
    union all
    select period, entity, 'COGS' as category, cogs as actual_amount from {{ ref('mart_monthly_pnl') }}
    union all
    select period, entity, 'Opex' as category, opex as actual_amount from {{ ref('mart_monthly_pnl') }}
    union all
    select period, entity, 'Operating Profit Proxy' as category, operating_profit_proxy as actual_amount from {{ ref('mart_monthly_pnl') }}
),
joined as (
    select
        a.period,
        a.entity,
        a.category,
        a.actual_amount,
        b.budget_amount,
        a.actual_amount - b.budget_amount as variance_amount,
        case when b.budget_amount = 0 or b.budget_amount is null then null else (a.actual_amount - b.budget_amount) / abs(b.budget_amount) end as variance_percent
    from actuals a
    left join {{ ref('stg_budget_normalized') }} b
        on a.period = b.period
        and a.entity = b.entity
        and a.category = b.category
)
select
    *,
    case
        when budget_amount is null then 'No Budget'
        when abs(coalesce(variance_percent, 0)) <= 0.05 then 'On Track'
        when category in ('Revenue', 'Operating Profit Proxy') and variance_amount > 0 then 'Favorable'
        when category in ('COGS', 'Opex') and variance_amount < 0 then 'Favorable'
        else 'Unfavorable'
    end as variance_status
from joined
