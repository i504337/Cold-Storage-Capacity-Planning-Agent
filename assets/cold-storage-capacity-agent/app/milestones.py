"""Business milestone instrumentation (M1–M5) for the cold storage capacity agent.

Extracted into a standalone module so that tests can import these functions
without pulling in the full agent stack (LangChain, LiteLLM, SAP SDK, etc.).
"""

import logging

logger = logging.getLogger(__name__)


def log_m1_achieved(storage_types: list, total_capacity: float, current_stock: float) -> None:
    logger.info(
        "M1.achieved: EWM capacity baseline loaded — storage types: %s, "
        "total physical capacity: %s, current stock: %s",
        storage_types, total_capacity, current_stock,
    )


def log_m1_missed(api_names: list) -> None:
    logger.warning(
        "M1.missed: EWM capacity baseline could not be established — "
        "API(s) failed or returned empty data: %s. Projection aborted.",
        api_names,
    )


def log_m2_achieved(count: int, storage_types: list, start_date: str, end_date: str, total_volume: float) -> None:
    logger.info(
        "M2.achieved: Inbound receipts projected — %d signals aggregated across %s, "
        "planning horizon: %s to %s, total inbound volume: %s",
        count, storage_types, start_date, end_date, total_volume,
    )


def log_m2_missed(signal_types: list) -> None:
    logger.warning(
        "M2.missed: Inbound receipt projection incomplete — one or more signal sources "
        "could not be read: %s. Projection may underestimate future capacity load.",
        signal_types,
    )


def log_m3_achieved(count: int, storage_types: list, start_date: str, end_date: str,
                    min_capacity: float, min_date: str) -> None:
    logger.info(
        "M3.achieved: Outbound issues projected — %d signals aggregated, net capacity computed "
        "for %s over %s to %s, minimum net capacity: %s on %s",
        count, storage_types, start_date, end_date, min_capacity, min_date,
    )


def log_m3_missed(signal_types: list) -> None:
    logger.warning(
        "M3.missed: Outbound issue projection incomplete — one or more signal sources "
        "could not be read: %s. Net capacity projection may overestimate available space.",
        signal_types,
    )


def log_m4_achieved(storage_type: str, query_date: str, available_capacity: float, latency_ms: int) -> None:
    logger.info(
        "M4.achieved: Query answered — storage_type: %s, query_date: %s, "
        "available_capacity: %s, response_latency_ms: %d",
        storage_type, query_date, available_capacity, latency_ms,
    )


def log_m4_missed(reason: str) -> None:
    logger.warning(
        "M4.missed: Query could not be answered — reason: %s. "
        "Clarification requested or error surfaced to user.",
        reason,
    )


def log_m5_achieved(order_number: str, order_type: str, material: str,
                    storage_type: str, delivery_date: str, overage: float,
                    suggested_action: str) -> None:
    logger.info(
        "M5.achieved: Breach alert raised — order: %s, type: %s, material: %s, "
        "storage_type: %s, delivery_date: %s, overage: %s, suggested_action: %s",
        order_number, order_type, material, storage_type,
        delivery_date, overage, suggested_action,
    )


def log_m5_missed(count: int, storage_types: list, start_date: str, end_date: str) -> None:
    logger.info(
        "M5.missed: Breach evaluation completed — no breach conditions detected across "
        "%d orders evaluated for storage_types: %s over horizon %s to %s.",
        count, storage_types, start_date, end_date,
    )
