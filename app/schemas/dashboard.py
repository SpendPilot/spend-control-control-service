from pydantic import BaseModel


class DashboardOverview(BaseModel):
    metrics: list[dict]
    monthly_spend: list[dict]
    category_spend: list[dict]
    top_vendors: list[dict]
    weekly_summary: dict

