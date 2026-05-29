select
    cast(year as integer) as year,
    cast(month as integer) as month,
    period,
    entity,
    cast(budget_revenue as double) as budget_revenue,
    cast(budget_cogs as double) as budget_cogs,
    cast(budget_opex as double) as budget_opex,
    cast(budget_ebitda as double) as budget_operating_profit_proxy
from raw_budget
