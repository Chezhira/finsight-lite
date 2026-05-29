select period, entity, 'Revenue' as category, budget_revenue as budget_amount from {{ ref('stg_budget') }}
union all
select period, entity, 'COGS' as category, budget_cogs as budget_amount from {{ ref('stg_budget') }}
union all
select period, entity, 'Opex' as category, budget_opex as budget_amount from {{ ref('stg_budget') }}
union all
select period, entity, 'Operating Profit Proxy' as category, budget_operating_profit_proxy as budget_amount from {{ ref('stg_budget') }}
