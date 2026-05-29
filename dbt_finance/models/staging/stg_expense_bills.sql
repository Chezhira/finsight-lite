select
    bill_ref,
    cast(bill_date as date) as bill_date,
    strftime(cast(bill_date as date), '%Y-%m') as period,
    entity,
    vendor,
    expense_category,
    cast(account_code as varchar) as account_code,
    account_name,
    cast(amount_kes as double) as amount_kes,
    currency,
    status,
    status in ('Outstanding', 'Partial') as is_open,
    status = 'Partial' as is_partial,
    status = 'Paid' as is_paid
from raw_expense_bills
