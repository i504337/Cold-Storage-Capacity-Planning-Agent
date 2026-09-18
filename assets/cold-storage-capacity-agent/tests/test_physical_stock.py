"""Unit test for CE_WHSEPHYSICALSTOCKPRODUCTS_0001 MCP tool — physical stock baseline."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_core.tools import StructuredTool


def make_mock_tool(name: str, response: dict) -> StructuredTool:
    async def _fn(**kwargs):
        return response
    return StructuredTool(
        name=name,
        description=f"Mock {name}",
        coroutine=_fn,
        func=lambda **kw: response,
        args_schema=None,
    )


@pytest.mark.asyncio
async def test_physical_stock_tool_returns_ewm_data():
    """Verify the physical stock tool returns expected EWM storage type and quantity fields."""
    mock_response = {
        "value": [
            {
                "EWMWarehouse": "WH01",
                "EWMStorageType": "CRYO",
                "Product": "BIOMED-001",
                "EWMStockQuantityInBaseUnit": "500.000",
                "EWMLoadingOrNetVolume": "0.250",
                "EWMLoadingOrNetVolumeUnit": "M3",
                "EWMStorageBinCapConsumptionVal": "5.000",
            }
        ]
    }
    tool = make_mock_tool("list_WarehousePhysicalStockProducts", mock_response)
    result = await tool.coroutine(EWMWarehouse="WH01", EWMStorageType="CRYO")
    assert result["value"][0]["EWMStorageType"] == "CRYO"
    assert result["value"][0]["Product"] == "BIOMED-001"
    assert float(result["value"][0]["EWMStockQuantityInBaseUnit"]) == 500.0


@pytest.mark.asyncio
async def test_physical_stock_empty_storage_type():
    """Verify empty result when storage type has no stock."""
    mock_response = {"value": []}
    tool = make_mock_tool("list_WarehousePhysicalStockProducts", mock_response)
    result = await tool.coroutine(EWMWarehouse="WH01", EWMStorageType="UCLD")
    assert result["value"] == []


@pytest.mark.asyncio
async def test_physical_stock_m1_logging(caplog):
    """Verify M1.achieved is logged when capacity baseline is loaded."""
    import logging
    import sys
    sys.path.insert(0, "app")
    from agent import log_m1_achieved
    with caplog.at_level(logging.INFO, logger="agent"):
        log_m1_achieved(["CRYO", "UCLD", "COLD"], 1000.0, 350.0)
    assert "M1.achieved" in caplog.text
    assert "CRYO" in caplog.text
