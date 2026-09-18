"""Unit test for WAREHOUSEORDER_0001 MCP tool — putaway and pick tasks."""
import pytest
from langchain_core.tools import StructuredTool


def make_mock_tool(name, response):
    async def _fn(**kwargs): return response
    return StructuredTool(name=name, description=f"Mock {name}", coroutine=_fn,
                          func=lambda **kw: response, args_schema=None)


@pytest.mark.asyncio
async def test_warehouse_task_putaway_fields():
    """Verify putaway warehouse task has destination storage type and target quantity."""
    mock_response = {
        "value": [
            {
                "EWMWarehouse": "WH01",
                "WarehouseTask": "000000000001",
                "WarehouseTaskItem": "0001",
                "WarehouseOrder": "0000000001",
                "WarehouseTaskStatus": "A",
                "WarehouseProcessCategory": "I",  # inbound/putaway
                "Product": "BIOMED-001",
                "TargetQuantityInBaseUnit": "100.000",
                "BaseUnit": "EA",
                "DestinationStorageType": "CRYO",
                "DestinationStorageBin": "CRYO-005",
                "WhseTaskPlannedClosingDateTime": "2026-09-26T10:00:00Z",
            }
        ]
    }
    tool = make_mock_tool("list_WarehouseTask", mock_response)
    result = await tool.coroutine(EWMWarehouse="WH01", WarehouseProcessCategory="I")
    task = result["value"][0]
    assert task["WarehouseProcessCategory"] == "I"
    assert task["DestinationStorageType"] == "CRYO"
    assert float(task["TargetQuantityInBaseUnit"]) == 100.0
    assert task["WarehouseTaskStatus"] == "A"  # open, not confirmed


@pytest.mark.asyncio
async def test_warehouse_task_pick_fields():
    """Verify pick task has source storage type for outbound capacity calculation."""
    pick_tasks = [
        {
            "WarehouseProcessCategory": "O",
            "SourceStorageType": "CRYO",
            "TargetQuantityInBaseUnit": "50.0",
            "WarehouseTaskStatus": "A",
        }
    ]
    open_picks = [t for t in pick_tasks if t["WarehouseTaskStatus"] != "C"]
    assert len(open_picks) == 1
    assert open_picks[0]["SourceStorageType"] == "CRYO"
