select
    period,
    entity,
    cast(opening_balance as double) as opening_balance,
    cast(inflows as double) as inflows,
    cast(outflows as double) as outflows,
    cast(closing_balance as double) as closing_balance,
    currency,
    cast(inflows as double) - cast(outflows as double) as net_cash_movement,
    cast(opening_balance as double) + cast(inflows as double) - cast(outflows as double) as calculated_closing_balance,
    cast(opening_balance as double) + cast(inflows as double) - cast(outflows as double) - cast(closing_balance as double) as cash_recon_difference
from raw_cash_movements
