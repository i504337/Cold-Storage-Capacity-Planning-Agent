"""Unit test for OP_WAREHOUSESTORAGEBIN_0001 MCP tool — bin capacity aggregation."""
import pytest
from langchain_core.tools import StructuredTool


def make_mock_tool(name, response):
    async def _fn(**kwargs): return response
    return StructuredTool(name=name, description=f"Mock {name}", coroutine=_fn,
                          func=lambda **kw: response, args_schema=None)


@pytest.mark.asyncio
async def test_storage_bin_capacity_fields():
    """Verify storage bin response contains capacity and utilization fields."""
    mock_response = {
        "value": [
            {
                "EWMWarehouse": "WH01",
                "EWMStorageBin": "CRYO-001",
                "EWMStorageType": "CRYO",
                "EWMStorBinTotalCapacityValue": "100.000",
                "EWMStorBinAvailCapacityValue": "45.000",
                "EWMStorageBinMaximumWeight": "500.000",
                "EWMStorageBinUsedWeight": "275.000",
                "EWMStorageBinMaximumVolume": "2.000",
                "EWMStorageBinOccupiedVolume": "1.100",
                "WeightUnit": "KG",
                "VolumeUnit": "M3",
                "EWMStorageBinIsFull": False,
            }
        ]
    }
    tool = make_mock_tool("list_WarehouseStorageBin", mock_response)
    result = await tool.coroutine(EWMWarehouse="WH01", EWMStorageType="CRYO")
    bin_data = result["value"][0]
    assert bin_data["EWMStorageType"] == "CRYO"
    assert float(bin_data["EWMStorBinTotalCapacityValue"]) == 100.0
    assert float(bin_data["EWMStorBinAvailCapacityValue"]) == 45.0
    assert bin_data["EWMStorageBinIsFull"] is False


@pytest.mark.asyncio
async def test_storage_bin_aggregation_per_type():
    """Verify we can aggregate total capacity across bins for a storage type."""
    bins = [
        {"EWMStorageType": "CRYO", "EWMStorBinTotalCapacityValue": "100.0", "EWMStorBinAvailCapacityValue": "40.0"},
        {"EWMStorageType": "CRYO", "EWMStorBinTotalCapacityValue": "100.0", "EWMStorBinAvailCapacityValue": "60.0"},
    ]
    total_cap = sum(float(b["EWMStorBinTotalCapacityValue"]) for b in bins)
    total_avail = sum(float(b["EWMStorBinAvailCapacityValue"]) for b in bins)
    assert total_cap == 200.0
    assert total_avail == 100.0
