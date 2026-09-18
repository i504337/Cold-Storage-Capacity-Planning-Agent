"""Unit test for WAREHOUSEAVAILABLESTOCK_0001 MCP tool."""
import pytest
from langchain_core.tools import StructuredTool


def make_mock_tool(name, response):
    async def _fn(**kwargs): return response
    return StructuredTool(name=name, description=f"Mock {name}", coroutine=_fn,
                          func=lambda **kw: response, args_schema=None)


@pytest.mark.asyncio
async def test_available_stock_returns_storage_type():
    """Verify available stock response includes storage type and quantity."""
    mock_response = {
        "value": [
            {
                "EWMWarehouse": "WH01",
                "Product": "BIOMED-001",
                "EWMStorageType": "CRYO",
                "EWMStorageBin": "CRYO-001",
                "AvailableEWMStockQty": "480.000",
                "EWMStockQuantityBaseUnit": "EA",
                "EWMStockType": "U1",
            }
        ]
    }
    tool = make_mock_tool("list_WarehouseAvailableStock", mock_response)
    result = await tool.coroutine(EWMWarehouse="WH01", EWMStorageType="CRYO")
    item = result["value"][0]
    assert item["EWMStorageType"] == "CRYO"
    assert float(item["AvailableEWMStockQty"]) == 480.0


@pytest.mark.asyncio
async def test_available_stock_multiple_products():
    """Verify multiple products in same storage type are returned."""
    mock_response = {
        "value": [
            {"Product": "BIOMED-001", "EWMStorageType": "CRYO", "AvailableEWMStockQty": "100.0"},
            {"Product": "BIOMED-002", "EWMStorageType": "CRYO", "AvailableEWMStockQty": "250.0"},
        ]
    }
    tool = make_mock_tool("list_WarehouseAvailableStock", mock_response)
    result = await tool.coroutine(EWMWarehouse="WH01")
    assert len(result["value"]) == 2
    total = sum(float(r["AvailableEWMStockQty"]) for r in result["value"])
    assert total == 350.0
