with gl as (
    select * from raw_gl_transactions
),
coa as (
    select * from {{ ref('stg_chart_of_accounts') }}
)
select
    gl.reference,
    cast(gl.date as date) as transaction_date,
    strftime(cast(gl.date as date), '%Y-%m') as period,
    gl.entity,
    cast(gl.account_code as varchar) as account_code,
    coalesce(coa.account_name, gl.account_name) as account_name,
    coa.account_type,
    coalesce(coa.category, gl.category) as category,
    gl.description,
    cast(gl.debit as double) as debit,
    cast(gl.credit as double) as credit,
    gl.currency,
    cast(gl.amount_kes as double) as amount_kes,
    case
        when lower(coalesce(coa.category, gl.category)) in ('revenue', 'other income') then cast(gl.credit as double) - cast(gl.debit as double)
        when lower(coalesce(coa.category, gl.category)) in ('cogs', 'cost of sales', 'opex', 'operating expenses', 'payroll', 'marketing', 'maintenance', 'professional fees', 'admin', 'logistics') then cast(gl.debit as double) - cast(gl.credit as double)
        else cast(gl.debit as double) - cast(gl.credit as double)
    end as signed_amount_kes,
    case
        when lower(coalesce(coa.category, gl.category)) in ('revenue', 'other income') then 'Revenue'
        when lower(coalesce(coa.category, gl.category)) in ('cogs', 'cost of sales') then 'COGS'
        when lower(coalesce(coa.category, gl.category)) in ('opex', 'operating expenses', 'payroll', 'marketing', 'maintenance', 'professional fees', 'admin', 'logistics') then 'Opex'
        else 'Balance Sheet'
    end as pnl_group,
    lower(coalesce(coa.account_type, '')) = 'p&l' or lower(coalesce(coa.category, gl.category)) in ('revenue', 'other income', 'cogs', 'cost of sales', 'opex', 'operating expenses', 'payroll', 'marketing', 'maintenance', 'professional fees', 'admin', 'logistics') as is_pnl_account,
    not (lower(coalesce(coa.account_type, '')) = 'p&l' or lower(coalesce(coa.category, gl.category)) in ('revenue', 'other income', 'cogs', 'cost of sales', 'opex', 'operating expenses', 'payroll', 'marketing', 'maintenance', 'professional fees', 'admin', 'logistics')) as is_balance_sheet_account
from gl
left join coa on cast(gl.account_code as varchar) = coa.account_code
