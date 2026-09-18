---
name: breach-detection
description: Evaluates all open inbound orders against projected net capacity for their planned delivery dates. Generates structured breach alerts when an order quantity is projected to exceed available cold storage capacity. Use this skill when a user asks about capacity breach risks, wants to know which orders will cause storage problems, or when proactively surfacing constraint risks during capacity analysis.
---

# Cold Storage Capacity Breach Detection

## Purpose

This skill identifies open inbound orders that will cause available cold storage capacity to be exceeded on their planned delivery date, and generates structured breach alerts for each one.

## Prerequisite

Before running breach detection, the capacity projection must be computed using the `capacity-projection` skill. Breach detection uses the net capacity values per (storage_type, date) from that projection.

## Step-by-Step Instructions

### Step 1: Gather Open Inbound Orders

Query all open orders that represent incoming stock to temperature-controlled storage types:

**Purchase Orders** — Call the **Purchase Order** tool:
- Filter: not completely delivered, delivery date within planning horizon
- For each PO schedule line: `PurchaseOrder`, `PurchaseOrderItem`, `Material`, `ScheduleLineDeliveryDate`, `OpenPurchaseOrderQuantity`, `PurchaseOrderQuantityUnit`
- Resolve material to storage type

**Stock Transport Orders** — Call the **Stock Transport Order** tool:
- Filter: not completely delivered, delivery date within planning horizon
- For each STO schedule line: `StockTransportOrder`, `StockTransportOrderItem`, `Product`, `ScheduleLineDeliveryDate`, `ScheduleLineOrderQuantity`
- Resolve product to storage type

**Inbound Deliveries** — Call the **Warehouse Inbound Delivery** tool:
- Filter: goods receipt not completed, planned delivery within horizon
- For each item: `EWMInboundDelivery`, `EWMInboundDeliveryItem`, `Product`, `PlannedDeliveryUTCDateTime`, `ProductQuantity`
- Resolve product to storage type

**Open Putaway Tasks** — Call the **Warehouse Order and Task** tool:
- Filter: putaway tasks not confirmed, planned closing within horizon
- For each task: `WarehouseTask`, `Product`, `WhseTaskPlannedClosingDateTime`, `TargetQuantityInBaseUnit`, `DestinationStorageType`

### Step 2: Evaluate Each Order Against Projected Capacity

For each open order:
1. Determine the `target_storage_type` (via material mapping or `DestinationStorageType`)
2. Look up `net_capacity[target_storage_type][delivery_date]` from the projection
3. Compute the **residual capacity** after this order arrives:
   ```
   residual = net_capacity[target_storage_type][delivery_date] - order_quantity_in_capacity_units
   ```
4. If `residual < 0`: **BREACH DETECTED**

### Step 3: Generate Breach Alerts

For each breach condition, create a structured alert:

```
BREACH ALERT
━━━━━━━━━━━━━━━━━━━━━━━━━━
Order Number:       {order_number}
Order Type:         {order_type}  (Purchase Order | STO | Inbound Delivery | Putaway Task)
Material/Product:   {material}
Planned Delivery:   {delivery_date}
Storage Type:       {storage_type_label} ({storage_type_code})
Available Capacity: {available_capacity} {unit}
Order Quantity:     {order_quantity} {unit}
Projected Overage:  {overage_amount} {unit}  (capacity will be exceeded by this amount)
━━━━━━━━━━━━━━━━━━━━━━━━━━
Suggested Actions:
  1. Split delivery into multiple smaller shipments spread over several days
  2. Reschedule delivery to a date when capacity is available
  3. Review open outbound deliveries to free up capacity before the delivery date
  4. Arrange temporary overflow storage in an alternative zone
```

### Step 4: Return Results

**If breaches found:**
- List all breach alerts sorted by delivery date (earliest first)
- Show a summary: "X breach alerts found across Y storage types. Earliest breach: [date] for [order] in [storage type]."

**If no breaches found:**
- Return: "No capacity breach conditions detected across {count} orders evaluated for {storage_types} over the period {start_date} to {end_date}. All incoming orders fit within projected available capacity."

## Logging

Always log the breach evaluation result — whether breaches were found or not:

**Breach found:**
`M5.achieved: Breach alert raised — order: {order_number}, type: {order_type}, material: {material}, storage_type: {value}, delivery_date: {date}, overage: {value}, suggested_action: Split delivery or reschedule`

**No breach found (normal state — still log it):**
`M5.missed: Breach evaluation completed — no breach conditions detected across {count} orders evaluated for storage_types: {list} over horizon {start_date} to {end_date}.`

## Important Notes

- A "miss" on M5 is **not an error** — it means no breach was found, which is the desired state
- Always evaluate ALL open orders, not just the one the user asked about
- Express the overage in the same capacity unit used throughout the projection
- Never suppress breach alerts — surface every detected overage, even small ones
- If a material cannot be mapped to a storage type, include it in the results with a note: "Storage type unknown — manually verify before delivery"
