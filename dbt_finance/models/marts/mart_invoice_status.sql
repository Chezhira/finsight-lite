select
    period,
    entity,
    status,
    count(*) as invoice_count,
    sum(amount_kes) as invoice_amount_kes
from {{ ref('stg_sales_invoices') }}
group by 1, 2, 3
