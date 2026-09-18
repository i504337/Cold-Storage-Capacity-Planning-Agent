# Cold Storage Capacity Planning Agent

AI-powered warehouse capacity planning assistant for temperature-controlled storage types in SAP EWM.

## Business challenge

Warehouse operations and sourcing personnel currently lack a consolidated, forward-looking view of storage capacity utilization for critical temperature-controlled storage facilities — cryo freezers (-80°C), ultra-cold refrigerators (-20°C), and controlled cold rooms (2–8°C) — configured as dedicated EWM storage types. The existing EWM capacity check operates at the individual storage bin level during putaway task creation and does not provide an aggregated, time-phased projection accounting for all incoming and outgoing material movements. This causes last-minute storage constraint incidents at the dock, forces laborious manual consolidation of multiple reports, and leaves buyers making procurement decisions without visibility into physical storage availability.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Last-minute storage constraint incidents at receiving dock | — | −95% | — | EWM Inbound Receiving | user |
| Order placement errors due to capacity oversight | — | Reduced | — | Procurement / Purchase Order Management | user |
| Manual report consolidation effort for capacity checks | 2–4 hrs/week | Eliminated | — | Warehouse Capacity Reporting | user |

## Key Milestones

1. **Storage type capacity baseline established** — Agent successfully reads current physical stock and bin-level capacity from EWM for all three storage types.
2. **Planned inbound receipts projected** — Agent correlates open POs, STOs, inbound deliveries, open putaway tasks, and planned/process orders onto a 1–2 week rolling horizon per storage type.
3. **Planned outbound issues projected** — Agent overlays open SOs, outbound deliveries, and open picking tasks to compute net available capacity.
4. **Natural language query answered** — Warehouse or sourcing user receives a correct, storage-type-specific capacity response to a plain-language question.
5. **Capacity breach alert raised** — Agent proactively flags an order whose quantity will exceed available capacity on its planned delivery date.

## Business Architecture (RBA)

### End-to-End Process

Plan to Fulfill — Life Sciences variant (Cell & Gene Therapy / Make to Stock life sciences)

### Process Hierarchy

```
Plan to Fulfill (E2E)
└── Manage Fulfillment (generic)
    └── Manage supply chain data and operations (BPS-342)
        └── Manage inventory and warehouse operations
└── Procure to Receipt (generic)
    └── Purchase products and services (BPS-329)
        └── Manage purchase order
```

### Summary

The business challenge maps primarily to Plan to Fulfill → Manage Fulfillment → Manage supply chain data and operations (BPS-342) for the EWM capacity projection and warehouse operations layer, and to Procure to Receipt → Purchase products and services (BPS-329) for the procurement signal integration (POs, STOs). Life sciences industry variants are the most directly applicable given the cryo/ultra-cold storage context.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Gap? | Notes / assumptions |
|---|---|---|---|---|---|---|
| View current physical stock by storage type | Internal Warehouse Management (S/4 CLD Private EWM, SC5130); Warehouse Physical Stock by Product API | `sap.s4:apiResource:CE_WHSEPHYSICALSTOCKPRODUCTS_0001:v1` | — | — | No | Standard API available; no MCP server — translation file required |
| Read storage bin capacity and utilization | Warehouse Storage Bin API | `sap.s4:apiResource:OP_WAREHOUSESTORAGEBIN_0001:v1` | — | — | No | Standard API available; no MCP server — translation file required |
| Read available warehouse stock | Warehouse Available Stock API | `sap.s4:apiResource:WAREHOUSEAVAILABLESTOCK_0001:v1` | — | — | No | Standard API available; no MCP server — translation file required |
| Project planned inbound receipts (POs, STOs) | Purchase Order Processing (SC5215); Stock Transport Order API | `sap.s4:apiResource:CE_PURCHASEORDER_0001:v1`, `sap.s4:apiResource:CE_STOCKTRANSPORTORDER_0001:v1` | — | — | No | Standard APIs available; no MCP servers |
| Project inbound deliveries and putaway tasks | Warehouse Inbound Delivery API; Warehouse Order and Task API | `sap.s4:apiResource:WAREHOUSEINBOUNDDELIVERY_0001:v1`, `sap.s4:apiResource:WAREHOUSEORDER_0001:v1` | — | — | No | Standard APIs available; no MCP servers |
| Project planned outbound issues (SOs, picking tasks) | Warehouse Outbound Delivery Order API | `sap.s4:apiResource:WAREHOUSEOUTBDELIVERYORDER_0001:v1` | — | — | No | Standard API available; no MCP server |
| Time-phased aggregated capacity projection across storage types | Warehouse Analytics (SC5646); Inventory Analytics (SC5474) | — | — | — | **Yes** | Standard EWM analytics are not time-phased across storage types; custom projection logic required in the agent |
| Natural language query interface for capacity | — | — | — | — | **Yes** | No native NL interface in EWM; requires AI Agent with LLM reasoning layer |
| Automated capacity breach alerting per order | — | — | — | — | **Yes** | No out-of-the-box cross-order-type breach alerting; agent must implement alert logic |
| Material-to-storage-type automatic mapping | Internal EWM configuration (storage section indicators, mixed storage rules) | — | — | — | Maybe | Mapping logic can be derived from EWM master data; agent must read and cache this |

### Key findings

- SAP S/4HANA Cloud Private Edition with EWM provides all required raw data APIs (stock, bins, deliveries, orders, tasks) — 8 relevant OData APIs identified, none with pre-built MCP servers; MCP translation files must be generated for each.
- Standard EWM analytics (Warehouse Analytics SC5646, Inventory Analytics SC5474) provide historical and near-real-time views but do **not** offer time-phased, aggregated projections across all order types and storage types — this is the core gap.
- No native natural language interface exists for EWM capacity queries — an AI Agent with LLM reasoning is the only viable approach to meet this requirement.
- Automated capacity breach alerting across POs, STOs, deliveries, and tasks simultaneously is not available out of the box — custom logic in the agent is required.
- Material-to-storage-type mapping can be derived from EWM master data (storage type search sequences, mixed storage indicators) and cached by the agent, avoiding the need for a separate configuration store.
- SAP Fieldglass and SAP Ariba capabilities returned in the fit-gap are not relevant to this scenario (non-workforce, no external procurement network required).

## Recommendations

### Cold Storage Capacity Planning AI Agent

#### Executive Summary

AI agent on SAP BTP providing NL capacity queries, time-phased projections, and breach alerts.

#### Recommended Solution

A Python-based AI Agent (A2A protocol) deployed on SAP BTP that:
1. Connects to SAP S/4HANA Cloud Private Edition via OData APIs to read current EWM stock, storage bin utilization, inbound/outbound deliveries, warehouse tasks, purchase orders, and stock transport orders.
2. Computes a rolling 1–2 week time-phased capacity projection per temperature-controlled storage type by overlaying planned receipts and issues onto current physical capacity.
3. Exposes a natural language interface allowing warehouse and sourcing personnel to ask plain-language capacity questions and receive structured, actionable answers.
4. Proactively generates capacity breach alerts when an order quantity is projected to exceed available storage on its planned delivery date.
5. Automatically resolves material-to-storage-type mapping from EWM master data.

MCP translation files are generated for each of the 8 identified EWM and Procurement OData APIs to enable tool-based access by the agent.

#### Problem Statement

Warehouse teams cannot anticipate storage constraint events because no system provides an aggregated, forward-looking capacity view across all temperature-controlled storage types. Buyers lack storage availability visibility at the time of purchase order creation, leading to constraint incidents at the receiving dock and costly manual workarounds.

#### Affected User Roles

- Sourcing Specialists / Buyers
- Warehouse Planners
- Warehouse Operators / Inbound Supervisors

#### Important factors

##### Eliminates manual report consolidation
The agent replaces the current 2–4 hours/week of manual report aggregation with instant, on-demand capacity answers via natural language.

##### Proactive breach alerting
Rather than reacting to constraints at the dock, the agent surfaces breach risks days in advance, giving buyers and planners time to adjust order quantities, delivery dates, or storage arrangements.

##### Non-invasive integration
The solution reads from existing EWM APIs without modifying SAP system configuration, making it low-risk to deploy and maintain.

#### Potential risks

##### API data latency
EWM OData APIs reflect near-real-time but not always instantaneous data; the agent's projections are as current as the last API poll. Caching strategy must balance freshness with API load.

##### Material-storage mapping complexity
If EWM master data for storage type assignments is inconsistent or incomplete, the agent's automatic mapping may require manual overrides or supplementary configuration input.

#### Recommended solution category

AI Agent

#### Intent fit
92%
