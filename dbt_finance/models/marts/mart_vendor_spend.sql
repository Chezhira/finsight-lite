select
    period,
    entity,
    vendor,
    expense_category,
    count(*) as bill_count,
    sum(amount_kes) as amount_kes
from {{ ref('stg_expense_bills') }}
group by 1, 2, 3, 4
