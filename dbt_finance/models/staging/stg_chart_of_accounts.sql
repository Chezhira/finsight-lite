select
    cast(account_code as varchar) as account_code,
    account_name,
    account_type,
    category
from raw_chart_of_accounts
