# Specification: cold-storage-capacity-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read `product-requirements-document.md` and `intent.md` thoroughly before starting implementation
- [x] Bootstrap agent code in `assets/cold-storage-capacity-agent/` using instructions from the `sap-agent-bootstrap` skill (invoke from inside `assets/cold-storage-capacity-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

The agent requires two runtime skills due to the complexity of its domain logic:

- [x] Create `assets/cold-storage-capacity-agent/app/skills/capacity-projection/SKILL.md` with:
  - **name**: `capacity-projection`
  - **description**: Step-by-step instructions for computing time-phased net capacity projections per storage type by overlaying inbound and outbound signals onto physical capacity
  - **Body**: Instructions covering how to:
    1. Read current physical stock per storage type (M1 baseline)
    2. Query all 5 inbound signal sources and aggregate by storage type and date (M2)
    3. Query all 3 outbound signal sources and compute net capacity per day (M3)
    4. Format the result as a date-ordered projection table
  - **allowed-tools**: list all 8 MCP tool names once resolved

- [x] Create `assets/cold-storage-capacity-agent/app/skills/breach-detection/SKILL.md` with:
  - **name**: `breach-detection`
  - **description**: Rules and logic for evaluating open orders against projected net capacity and generating breach alerts
  - **Body**: Instructions covering how to:
    1. For each open inbound order (PO, STO, inbound delivery, warehouse task), compute: projected stock on delivery date + inbound order quantity
    2. Compare against physical capacity of the target storage type
    3. If overflow detected: generate structured breach alert with order number, type, material, delivery date, storage type, overage quantity, and suggested action
    4. Return list of all breach alerts or empty list if none detected (M5 log either way)

---

## Project-Specific Tasks

### Storage Type Configuration

- [ ] Create `assets/cold-storage-capacity-agent/app/skills/capacity-projection/references/storage-type-registry.json` — externally configurable registry mapping EWM storage type codes to temperature zones:
  ```json
  {
    "storage_types": [
      {"code": "CRYO", "label": "Cryo Freezer", "temperature": "-80°C"},
      {"code": "UCLD", "label": "Ultra-Cold Refrigerator", "temperature": "-20°C"},
      {"code": "COLD", "label": "Cold Room", "temperature": "2-8°C"}
    ]
  }
  ```
  Note: Actual EWM storage type codes must be confirmed with the customer's EWM configuration. These are placeholders.

### Material-to-Storage-Type Mapping

- [ ] Implement material-to-storage-type resolution logic in the agent's system prompt and skill: the agent must query `OP_WAREHOUSESTORAGEBIN_0001` and `CE_WHSEPHYSICALSTOCKPRODUCTS_0001` to derive which storage type a material is assigned to, based on where it currently lives in EWM
- [ ] If a material has no stock in any temperature-controlled storage type, the agent must surface this as an explicit data gap — never default silently

### Natural Language Query Interface (REQ-01)

- [ ] Implement system prompt in `app/agent.py` with the following instructions:
  - You are a cold storage capacity planning assistant for temperature-controlled warehouse storage types: cryo freezers (−80°C), ultra-cold refrigerators (−20°C), and cold rooms (2–8°C).
  - When users ask about storage capacity, always resolve the relevant storage type from EWM master data.
  - IMPORTANT: You MUST use tools to retrieve live data. Never fabricate, guess, or invent data. Relay tool errors verbatim without adding suggestions.
  - When calling tools that support pagination, always set the page size parameter (`top`, `limit`, `pageSize`) to a maximum of 100 items.
  - If a query is ambiguous (storage type unclear, date range not specified), ask a clarifying question before retrieving data.
  - Always clearly state when projections are estimates based on open order data, not confirmed physical facts.

### Time-Phased Capacity Projection (REQ-02, REQ-03, REQ-04)

- [ ] Implement projection computation in the `capacity-projection` skill:
  - Default horizon: today + 14 days (configurable via user input)
  - Net capacity formula per storage type per day: `physical_capacity − current_stock − planned_receipts + planned_issues`
  - Planned receipts = open PO quantities (by schedule line delivery date) + open STO quantities (by schedule line delivery date) + open inbound delivery quantities (by planned delivery date) + open putaway warehouse task quantities (by planned closing date) — all filtered to temperature-controlled storage types only
  - Planned issues = open outbound delivery order quantities (by planned goods issue date) + open pick warehouse task quantities (by planned closing date)
  - Express all quantities in a consistent capacity unit (volume preferred; weight as fallback). Convert units using the item's weight/volume fields from the API response.

### Capacity Breach Alert (REQ-06)

- [ ] Implement breach evaluation in the `breach-detection` skill:
  - Evaluate all open POs, STOs, inbound deliveries, and putaway tasks
  - For each order: check if (projected stock on delivery date + order quantity) > physical capacity of target storage type
  - Generate breach alerts with fields: `order_number`, `order_type`, `material`, `planned_delivery_date`, `storage_type`, `projected_overage`, `suggested_action`
  - Suggested actions to include: "Split delivery", "Reschedule delivery date", "Arrange temporary overflow storage", "Review open outbound orders to free capacity"
  - Expose breach alerts via: (1) proactive display when query context implies inbound planning, (2) explicit user query "show all breach alerts" or similar

### MCP Tool Integration (8 APIs — Path A)

- [ ] Invoke `mcp-translation-file` skill for each of the 8 API spec files in `specification/cold-storage-capacity-agent/api-specs/`:
  1. `CE_WHSEPHYSICALSTOCKPRODUCTS_0001.edmx` — ORD ID: `sap.s4:apiResource:CE_WHSEPHYSICALSTOCKPRODUCTS_0001:v1`
  2. `OP_WAREHOUSESTORAGEBIN_0001.edmx` — ORD ID: `sap.s4:apiResource:OP_WAREHOUSESTORAGEBIN_0001:v1`
  3. `WAREHOUSEAVAILABLESTOCK_0001.edmx` — ORD ID: `sap.s4:apiResource:WAREHOUSEAVAILABLESTOCK_0001:v1`
  4. `CE_PURCHASEORDER_0001.edmx` — ORD ID: `sap.s4:apiResource:CE_PURCHASEORDER_0001:v1`
  5. `CE_STOCKTRANSPORTORDER_0001.edmx` — ORD ID: `sap.s4:apiResource:CE_STOCKTRANSPORTORDER_0001:v1`
  6. `WAREHOUSEINBOUNDDELIVERY_0001.edmx` — ORD ID: `sap.s4:apiResource:WAREHOUSEINBOUNDDELIVERY_0001:v1`
  7. `WAREHOUSEORDER_0001.edmx` — ORD ID: `sap.s4:apiResource:WAREHOUSEORDER_0001:v1`
  8. `WAREHOUSEOUTBDELIVERYORDER_0001.edmx` — ORD ID: `sap.s4:apiResource:WAREHOUSEOUTBDELIVERYORDER_0001:v1`
- [ ] Invoke `setup-solution` skill to register MCP server assets for all 8 translation files
- [ ] After `setup-solution` completes, read each generated `asset.yaml` and copy the exact `ordId` values — use these verbatim in the agent's `asset.yaml` `requires` section. NEVER invent or guess ORD IDs.
- [ ] Wire MCP tool loading in `agent.py` using `get_mcp_tools()` from the bootstrap-generated `mcp_tools` module
- [ ] Add all 8 MCP server `requires` entries to `assets/cold-storage-capacity-agent/asset.yaml`

---

## Business Instrumentation

- [ ] Implement structured logging and OpenTelemetry spans for all 5 PRD milestones:

  **M1 — Storage Type Capacity Baseline Established**
  - Span: `m1_capacity_baseline`
  - Log on achievement: `M1.achieved: EWM capacity baseline loaded — storage types: {list}, total physical capacity: {value}, current stock: {value}`
  - Log on miss: `M1.missed: EWM capacity baseline could not be established — API(s) failed or returned empty data: {api_names}. Projection aborted.`

  **M2 — Planned Inbound Receipts Projected**
  - Span: `m2_inbound_projection`
  - Log on achievement: `M2.achieved: Inbound receipts projected — {count} signals aggregated across {storage_types}, planning horizon: {start_date} to {end_date}, total inbound volume: {value}`
  - Log on miss: `M2.missed: Inbound receipt projection incomplete — one or more signal sources could not be read: {signal_types}. Projection may underestimate future capacity load.`

  **M3 — Planned Outbound Issues Projected**
  - Span: `m3_outbound_projection`
  - Log on achievement: `M3.achieved: Outbound issues projected — {count} signals aggregated, net capacity computed for {storage_types} over {start_date} to {end_date}, minimum net capacity: {value} on {date}`
  - Log on miss: `M3.missed: Outbound issue projection incomplete — one or more signal sources could not be read: {signal_types}. Net capacity projection may overestimate available space.`

  **M4 — Natural Language Query Answered**
  - Span: `m4_query_answered`
  - Log on achievement: `M4.achieved: Query answered — storage_type: {value}, query_date: {value}, available_capacity: {value}, response_latency_ms: {value}`
  - Log on miss: `M4.missed: Query could not be answered — reason: {ambiguous_intent|missing_material_mapping|api_failure|projection_error}. Clarification requested or error surfaced to user.`

  **M5 — Capacity Breach Alert Raised**
  - Span: `m5_breach_alert`
  - Log on achievement: `M5.achieved: Breach alert raised — order: {order_number}, type: {order_type}, material: {material}, storage_type: {value}, delivery_date: {date}, overage: {value}, suggested_action: {text}`
  - Log on miss (no breach found — normal state): `M5.missed: Breach evaluation completed — no breach conditions detected across {count} orders evaluated for storage_types: {list} over horizon {start_date} to {end_date}.`

- [ ] Extract all business logic from `stream()` into a plain async helper method `_run_agent()` to avoid `GeneratorExit` context errors with OpenTelemetry spans
- [ ] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## Mock Config

- [ ] After all MCP translation files and `setup-solution` complete, invoke `mcp-mock-config` skill to generate `mcp-mock.json` — required before tests can run

---

## Testing

- [ ] `conftest.py` only sets `IBD_TESTING=true`
- [ ] Write unit tests in `assets/cold-storage-capacity-agent/tests/` — exactly one per MCP tool (8 tools = 8 unit tests minimum), run each immediately after writing:
  1. `test_physical_stock.py` — mock `CE_WHSEPHYSICALSTOCKPRODUCTS_0001` tool, verify capacity baseline loading
  2. `test_storage_bin.py` — mock `OP_WAREHOUSESTORAGEBIN_0001` tool, verify bin capacity aggregation per storage type
  3. `test_available_stock.py` — mock `WAREHOUSEAVAILABLESTOCK_0001` tool, verify available stock query
  4. `test_purchase_order.py` — mock `CE_PURCHASEORDER_0001` tool, verify PO schedule line extraction and date mapping
  5. `test_stock_transport_order.py` — mock `CE_STOCKTRANSPORTORDER_0001` tool, verify STO schedule line extraction
  6. `test_inbound_delivery.py` — mock `WAREHOUSEINBOUNDDELIVERY_0001` tool, verify inbound delivery item aggregation
  7. `test_warehouse_order.py` — mock `WAREHOUSEORDER_0001` tool, verify putaway and pick task extraction
  8. `test_outbound_delivery.py` — mock `WAREHOUSEOUTBDELIVERYORDER_0001` tool, verify outbound delivery quantity extraction
- [ ] Write one integration test `test_end_to_end.py` executing full agent flow:
  - User query: "How much cryo freezer space will we have next week?"
  - Mock all 8 MCP tools with sample data
  - Mock LLM responses
  - Assert agent returns a capacity answer with storage type, date, and available capacity values
  - Assert M4.achieved log is emitted
- [ ] Write one breach alert integration test `test_breach_detection.py`:
  - Inject a PO whose quantity exceeds projected capacity on its delivery date
  - Assert M5.achieved log is emitted
  - Assert breach alert contains correct fields
- [ ] Run `pytest` from `assets/cold-storage-capacity-agent/` (no args, no extra flags)
- [ ] If coverage < 70%, add targeted tests until threshold met
- [ ] Verify `assets/cold-storage-capacity-agent/app/agent.py` has exactly 9 decorated functions — run: `grep -c "^@agent_model\|^@agent_config\|^@prompt_section" assets/cold-storage-capacity-agent/app/agent.py` and confirm it returns 9
- [ ] Run `pytest` again (no args) to generate final `test_report.json`
- [ ] Verify `test_report.json` exists in `assets/cold-storage-capacity-agent/`
