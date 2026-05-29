select
    invoice_ref,
    cast(invoice_date as date) as invoice_date,
    strftime(cast(invoice_date as date), '%Y-%m') as period,
    entity,
    customer,
    revenue_category,
    cast(amount_kes as double) as amount_kes,
    cast(amount_usd as double) as amount_usd,
    currency,
    status,
    status in ('Outstanding', 'Partial') as is_open,
    status = 'Partial' as is_partial,
    status = 'Paid' as is_paid
from raw_sales_invoices
