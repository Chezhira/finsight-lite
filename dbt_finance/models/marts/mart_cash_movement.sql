select
    period,
    entity,
    opening_balance,
    inflows,
    outflows,
    net_cash_movement,
    closing_balance,
    cash_recon_difference
from {{ ref('stg_cash_movements') }}
