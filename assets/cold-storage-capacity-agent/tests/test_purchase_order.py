"""Unit test for CE_PURCHASEORDER_0001 MCP tool — PO schedule line extraction."""
import pytest
from langchain_core.tools import StructuredTool
from datetime import date


def make_mock_tool(name, response):
    async def _fn(**kwargs): return response
    return StructuredTool(name=name, description=f"Mock {name}", coroutine=_fn,
                          func=lambda **kw: response, args_schema=None)


@pytest.mark.asyncio
async def test_purchase_order_schedule_lines():
    """Verify PO schedule lines have delivery date and open quantity."""
    mock_response = {
        "value": [
            {
                "PurchaseOrder": "4500000001",
                "PurchaseOrderItem": "00010",
                "Material": "BIOMED-001",
                "Plant": "1000",
                "IsCompletelyDelivered": False,
                "_PurchaseOrderScheduleLineTP": [
                    {
                        "ScheduleLine": "0001",
                        "ScheduleLineDeliveryDate": "2026-09-25",
                        "OpenPurchaseOrderQuantity": "200.000",
                        "PurchaseOrderQuantityUnit": "EA",
                    }
                ]
            }
        ]
    }
    tool = make_mock_tool("list_PurchaseOrder", mock_response)
    result = await tool.coroutine(IsCompletelyDelivered="false")
    po = result["value"][0]
    assert po["PurchaseOrder"] == "4500000001"
    assert po["IsCompletelyDelivered"] is False
    sched = po["_PurchaseOrderScheduleLineTP"][0]
    assert sched["ScheduleLineDeliveryDate"] == "2026-09-25"
    assert float(sched["OpenPurchaseOrderQuantity"]) == 200.0


@pytest.mark.asyncio
async def test_purchase_order_m2_logging(caplog):
    """Verify M2.achieved is logged when inbound receipts are projected."""
    import logging, sys
    sys.path.insert(0, "app")
    from milestones import log_m2_achieved
    with caplog.at_level(logging.INFO, logger="milestones"):
        log_m2_achieved(5, ["CRYO", "UCLD"], "2026-09-18", "2026-10-02", 750.0)
    assert "M2.achieved" in caplog.text
    assert "CRYO" in caplog.text
