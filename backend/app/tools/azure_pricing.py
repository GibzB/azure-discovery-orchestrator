"""
Tool: Azure Retail Pricing API wrapper
"""
import httpx


async def get_azure_pricing(service_name: str, region: str = "eastus") -> list[dict]:
    """Fetch retail pricing for an Azure service in a given region."""
    url = "https://prices.azure.com/api/retail/prices"
    params = {
        "$filter": f"serviceName eq '{service_name}' and armRegionName eq '{region}'",
        "$top": 20,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("Items", [])
