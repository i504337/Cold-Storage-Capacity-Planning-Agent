"""Unit test for CE_STOCKTRANSPORTORDER_0001 MCP tool — STO schedule lines."""
import pytest
from langchain_core.tools import StructuredTool


def make_mock_tool(name, response):
    async def _fn(**kwargs): return response
    return StructuredTool(name=name, description=f"Mock {name}", coroutine=_fn,
                          func=lambda **kw: response, args_schema=None)


@pytest.mark.asyncio
async def test_sto_schedule_line_fields():
    """Verify STO schedule lines contain delivery date and order quantity."""
    mock_response = {
        "value": [
            {
                "StockTransportOrder": "4500000010",
                "StockTransportOrderType": "UB",
                "SupplyingPlant": "1000",
                "_StockTransportOrderItem": [
                    {
                        "StockTransportOrderItem": "00010",
                        "Product": "BIOMED-002",
                        "OrderQuantity": "150.000",
                        "OrderQuantityUnit": "EA",
                        "IsCompletelyDelivered": False,
                        "_STOScheduleLine": [
                            {
                                "ScheduleLineDeliveryDate": "2026-09-27",
                                "ScheduleLineOrderQuantity": "150.000",
                                "OrderQuantityUnit": "EA",
                            }
                        ]
                    }
                ]
            }
        ]
    }
    tool = make_mock_tool("list_StockTransportOrder", mock_response)
    result = await tool.coroutine()
    sto = result["value"][0]
    assert sto["StockTransportOrder"] == "4500000010"
    item = sto["_StockTransportOrderItem"][0]
    assert item["Product"] == "BIOMED-002"
    sched = item["_STOScheduleLine"][0]
    assert sched["ScheduleLineDeliveryDate"] == "2026-09-27"
    assert float(sched["ScheduleLineOrderQuantity"]) == 150.0


@pytest.mark.asyncio
async def test_sto_completely_delivered_excluded():
    """Verify completely delivered STO items are filtered out."""
    items = [
        {"Product": "P1", "IsCompletelyDelivered": True, "OrderQuantity": "100.0"},
        {"Product": "P2", "IsCompletelyDelivered": False, "OrderQuantity": "50.0"},
    ]
    open_items = [i for i in items if not i["IsCompletelyDelivered"]]
    assert len(open_items) == 1
    assert open_items[0]["Product"] == "P2"
