from types import MappingProxyType


MEMBERSHIP_PLANS = MappingProxyType(
    {
        "basic": MappingProxyType(
            {
                "name": "BASIC",
                "monthly_price": 1200,
            }
        ),
        "pro": MappingProxyType(
            {
                "name": "PRO",
                "monthly_price": 1500,
            }
        ),
        "elite": MappingProxyType(
            {
                "name": "ELITE",
                "monthly_price": 2500,
            }
        ),
    }
)

MEMBERSHIP_DURATIONS = (1, 3, 6)


def plan_price(plan_type: str, duration_months: int) -> int:
    return MEMBERSHIP_PLANS[plan_type]["monthly_price"] * duration_months
