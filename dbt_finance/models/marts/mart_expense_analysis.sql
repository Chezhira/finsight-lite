select
    period,
    entity,
    vendor,
    expense_category,
    status,
    amount_kes,
    currency
from {{ ref('stg_expense_bills') }}
