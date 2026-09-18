---
name: capacity-projection
description: Computes time-phased net capacity projections per temperature-controlled EWM storage type by overlaying planned inbound receipts and outbound issues onto current physical stock. Use this skill when a user asks about projected available storage capacity, future capacity trends, or wants to plan inbound deliveries against available cold storage space.
---

# Cold Storage Capacity Projection

## Purpose

This skill computes a rolling 1–2 week time-phased capacity projection for each temperature-controlled storage type (cryo freezer, ultra-cold refrigerator, cold room) by:
1. Establishing the current physical capacity baseline (M1)
2. Projecting all planned inbound receipts onto the horizon (M2)
3. Overlaying all planned outbound issues and computing net available capacity per day (M3)

## Storage Type Registry

Temperature-controlled storage types are defined in `references/storage-type-registry.json`. Load it with the `load` tool if you need the list of valid storage type codes and labels.

## Step-by-Step Instructions

### Step 1: Establish Capacity Baseline (M1)

1. Call the **Warehouse Storage Bin** tool to read all storage bins for the warehouse and the target storage type(s). Filter for bins belonging to temperature-controlled storage types only.
   - Key fields: `EWMWarehouse`, `EWMStorageType`, `EWMStorBinTotalCapacityValue`, `EWMStorBinAvailCapacityValue`, `EWMStorageBinMaximumWeight`, `EWMStorageBinUsedWeight`, `EWMStorageBinMaximumVolume`, `EWMStorageBinOccupiedVolume`
   - Aggregate total physical capacity per storage type by summing `EWMStorBinTotalCapacityValue` (or weight/volume depending on what is configured)

2. Call the **Warehouse Physical Stock by Product** tool to read current physical stock per storage type.
   - Key fields: `EWMWarehouse`, `EWMStorageType`, `Product`, `EWMStockQuantityInBaseUnit`, `EWMLoadingOrNetWeight`, `EWMLoadingOrNetVolume`, `EWMStorageBinCapConsumptionVal`
   - Aggregate current stock per storage type

3. Call the **Warehouse Available Stock** tool to cross-check available quantities per product and storage type.
   - Key fields: `EWMWarehouse`, `EWMStorageType`, `Product`, `AvailableEWMStockQty`

4. Log: `M1.achieved: EWM capacity baseline loaded — storage types: {list}, total physical capacity: {value}, current stock: {value}`
   - If any API call fails: `M1.missed: EWM capacity baseline could not be established — API(s) failed or returned empty data: {api_names}. Projection aborted.`

### Step 2: Project Planned Inbound Receipts (M2)

For each of the 5 inbound signal sources, query open records and map quantities to storage type and delivery date:

**Source 1 — Purchase Orders**
- Call the **Purchase Order** tool. Filter for open POs (not completely delivered).
- Navigate to schedule lines: `ScheduleLineDeliveryDate` + `OpenPurchaseOrderQuantity`
- Resolve material to storage type (see Material Mapping below)
- Only include items whose resolved storage type is temperature-controlled

**Source 2 — Stock Transport Orders**
- Call the **Stock Transport Order** tool. Filter for open STOs.
- Navigate to schedule lines: `ScheduleLineDeliveryDate` + `ScheduleLineOrderQuantity`
- Resolve material to storage type

**Source 3 — Inbound Deliveries**
- Call the **Warehouse Inbound Delivery** tool. Filter for items not yet goods-receipted (`GoodsReceiptStatus` ≠ completed).
- Key fields: `PlannedDeliveryUTCDateTime`, `ProductQuantity`, `Product`
- Resolve product to storage type

**Source 4 — Open Putaway Tasks**
- Call the **Warehouse Order and Task** tool. Filter for warehouse tasks with `WarehouseProcessCategory` = putaway and `WarehouseTaskStatus` ≠ confirmed.
- Key fields: `WhseTaskPlannedClosingDateTime`, `TargetQuantityInBaseUnit`, `Product`, `DestinationStorageType`
- `DestinationStorageType` directly gives the target storage type — no mapping needed

**Source 5 — Planned/Process Orders** (if available)
- Note: Planned and process orders feed into inbound deliveries or warehouse tasks before arriving at EWM. If no dedicated planned order API is connected, capture these through the inbound delivery signal above.

Aggregate: for each (storage_type, date) pair, sum all inbound quantities. Express in the same capacity unit as the baseline.

Log: `M2.achieved: Inbound receipts projected — {count} signals aggregated across {storage_types}, planning horizon: {start_date} to {end_date}, total inbound volume: {value}`
- On partial failure: `M2.missed: Inbound receipt projection incomplete — one or more signal sources could not be read: {signal_types}. Projection may underestimate future capacity load.`

### Step 3: Project Planned Outbound Issues and Compute Net Capacity (M3)

**Source 1 — Outbound Delivery Orders**
- Call the **Warehouse Outbound Delivery Order** tool. Filter for items not yet goods-issued (`GoodsIssueStatus` ≠ completed).
- Key fields: `PlndGoodsIssueStartUTCDateTime`, `ProductQuantity`, `Product`, `EWMStorageType`
- `EWMStorageType` gives the source storage type directly

**Source 2 — Open Pick Tasks**
- Call the **Warehouse Order and Task** tool. Filter for tasks with `WarehouseProcessCategory` = picking and `WarehouseTaskStatus` ≠ confirmed.
- Key fields: `WhseTaskPlannedClosingDateTime`, `TargetQuantityInBaseUnit`, `Product`, `SourceStorageType`
- `SourceStorageType` gives the storage type the goods are leaving from

Aggregate outbound quantities per (storage_type, date).

**Net Capacity Formula** (per storage type, per day):
```
net_capacity[storage_type][date] = physical_capacity[storage_type]
  - current_stock[storage_type]
  - cumulative_inbound[storage_type][date]   # all inbound up to and including this date
  + cumulative_outbound[storage_type][date]  # all outbound up to and including this date
```

Present results as a date-ordered table showing:
- Date
- Storage Type
- Physical Capacity
- Current Stock
- Planned Inbound (cumulative to that date)
- Planned Outbound (cumulative to that date)
- Net Available Capacity
- Utilization %

Log: `M3.achieved: Outbound issues projected — {count} signals aggregated, net capacity computed for {storage_types} over {start_date} to {end_date}, minimum net capacity: {value} on {date}`
- On partial failure: `M3.missed: Outbound issue projection incomplete — one or more signal sources could not be read: {signal_types}. Net capacity projection may overestimate available space.`

## Material-to-Storage-Type Mapping

To resolve a material to its target storage type:
1. Check physical stock records (`CE_WHSEPHYSICALSTOCKPRODUCTS_0001`): find which `EWMStorageType` the material currently lives in
2. If the material has no current stock, check recent inbound delivery records for its usual destination storage type
3. If still unresolved, report explicitly: "Material {X} has no confirmed storage type assignment in EWM. Please confirm the correct storage zone before including it in the projection."
4. **Never default silently to a storage type** — always surface unknown mappings as explicit data gaps

## Capacity Unit Harmonization

- Prefer **capacity consumption value** (`EWMStorBinAvailCapacityValue`, `EWMStorageBinCapConsumptionVal`) when available — this is dimensionless and already comparable across bins
- Fall back to **volume** (cubic meters or liters) if capacity consumption values are not set
- Fall back to **weight** (kg) as last resort
- Always state which unit is being used in the response

## Response Format

Always label projections clearly: "This projection is based on open order data as of [timestamp] and reflects planned — not confirmed — movements. Actual capacity may differ."
