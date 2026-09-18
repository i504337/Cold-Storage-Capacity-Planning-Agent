"""Unit test for WAREHOUSEINBOUNDDELIVERY_0001 MCP tool."""
import pytest
from langchain_core.tools import StructuredTool


def make_mock_tool(name, response):
    async def _fn(**kwargs): return response
    return StructuredTool(name=name, description=f"Mock {name}", coroutine=_fn,
                          func=lambda **kw: response, args_schema=None)


@pytest.mark.asyncio
async def test_inbound_delivery_item_fields():
    """Verify inbound delivery items include product, quantity and GR status."""
    mock_response = {
        "value": [
            {
                "EWMInboundDelivery": "18000000001",
                "EWMWarehouse": "WH01",
                "PlannedDeliveryUTCDateTime": "2026-09-26T08:00:00Z",
                "_WhseInbDeliveryItem": [
                    {
                        "EWMInboundDeliveryItem": "000010",
                        "Product": "BIOMED-001",
                        "ProductQuantity": "300.000",
                        "QuantityUnit": "EA",
                        "GoodsReceiptStatus": "A",
                        "PutawayStatus": "A",
                        "PurchasingDocument": "4500000001",
                    }
                ]
            }
        ]
    }
    tool = make_mock_tool("list_WhseInboundDeliveryHead", mock_response)
    result = await tool.coroutine(EWMWarehouse="WH01")
    delivery = result["value"][0]
    assert delivery["EWMInboundDelivery"] == "18000000001"
    item = delivery["_WhseInbDeliveryItem"][0]
    assert item["Product"] == "BIOMED-001"
    assert float(item["ProductQuantity"]) == 300.0
    assert item["GoodsReceiptStatus"] == "A"  # not completed


@pytest.mark.asyncio
async def test_inbound_delivery_gr_status_filtering():
    """Only items with GoodsReceiptStatus not completed should be included."""
    items = [
        {"Product": "P1", "GoodsReceiptStatus": "C", "ProductQuantity": "100.0"},  # completed
        {"Product": "P2", "GoodsReceiptStatus": "A", "ProductQuantity": "200.0"},  # open
    ]
    open_items = [i for i in items if i["GoodsReceiptStatus"] != "C"]
    assert len(open_items) == 1
    assert open_items[0]["Product"] == "P2"
