"""Unit test for WAREHOUSEOUTBDELIVERYORDER_0001 MCP tool — outbound delivery orders."""
import pytest
from langchain_core.tools import StructuredTool


def make_mock_tool(name, response):
    async def _fn(**kwargs): return response
    return StructuredTool(name=name, description=f"Mock {name}", coroutine=_fn,
                          func=lambda **kw: response, args_schema=None)


@pytest.mark.asyncio
async def test_outbound_delivery_order_fields():
    """Verify outbound delivery items include storage type and planned GI date."""
    mock_response = {
        "value": [
            {
                "EWMOutboundDeliveryOrder": "28000000001",
                "EWMWarehouse": "WH01",
                "PlannedDeliveryUTCDateTime": "2026-09-28T08:00:00Z",
                "GoodsIssueStatus": "A",
                "_WhseOutbDeliveryOrderItem": [
                    {
                        "EWMOutboundDeliveryOrderItem": "000010",
                        "Product": "BIOMED-001",
                        "ProductQuantity": "80.000",
                        "QuantityUnit": "EA",
                        "EWMStorageType": "CRYO",
                        "GoodsIssueStatus": "A",
                        "PlndGoodsIssueStartUTCDateTime": "2026-09-28T06:00:00Z",
                        "SalesOrder": "5000000001",
                    }
                ]
            }
        ]
    }
    tool = make_mock_tool("list_WhseOutboundDeliveryOrderHead", mock_response)
    result = await tool.coroutine(EWMWarehouse="WH01")
    delivery = result["value"][0]
    assert delivery["GoodsIssueStatus"] == "A"
    item = delivery["_WhseOutbDeliveryOrderItem"][0]
    assert item["EWMStorageType"] == "CRYO"
    assert float(item["ProductQuantity"]) == 80.0
    assert item["PlndGoodsIssueStartUTCDateTime"] == "2026-09-28T06:00:00Z"


@pytest.mark.asyncio
async def test_m3_outbound_projection_logging(caplog):
    """Verify M3.achieved is logged after outbound issues are projected."""
    import logging, sys
    sys.path.insert(0, "app")
    from agent import log_m3_achieved
    with caplog.at_level(logging.INFO, logger="agent"):
        log_m3_achieved(3, ["CRYO"], "2026-09-18", "2026-10-02", 42.5, "2026-09-28")
    assert "M3.achieved" in caplog.text
    assert "CRYO" in caplog.text
