"""Constants for the Saphir X Pool integration."""

from __future__ import annotations

DOMAIN = "saphir_x"

DEFAULT_PORT = 8888
DEFAULT_SCAN_INTERVAL = 30  # seconds

CONF_USERNAME = "username"  # Saphir device code, e.g. "12345"
CONF_PASSWORD = "password"

# Value read back from a register when the corresponding sensor is not
# installed / disabled on the controller.
SENTINEL_NA = 9999

# Data numbers that the coordinator polls every update cycle.
# (read-only measurements + diagnostics + read/write setpoints & state)
POLL_NUMBERS: tuple[str, ...] = (
    # measurements
    "006", "007", "008", "009", "010", "011", "012",
    "020", "021", "022", "023", "030",
    # setpoints / amounts (read part of RW)
    "200", "240", "241", "290", "110", "247", "223", "102", "222",
    # diagnostics
    "001", "002", "003", "004",
)

# Relay control register (CAN module relay outputs 12-16, written as a bitmask;
# the controller toggles the addressed relay). Device uses register 132.
RELAY_REGISTER = "132"
RELAY_BITCODE = {
    "counter_current": 8,   # 12 GEGENSTROM
    "massage": 16,          # 13 MASSAGE
    "cover_open": 32,       # 14 ROLLO_OPEN
    "cover_close": 64,      # 15 ROLLO_CLOSE
    "light": 128,           # 16 LIGHT
}

# data number 030 — current fault code
ERROR_CODES: dict[int, str] = {
    0: "ok",
    1: "rtc_clk",
    2: "parameter",
    3: "no_timeset",
    4: "ph_out_of_range",
    5: "cu_empty",
    6: "ph_empty",
    7: "h2o2_empty",
    8: "cu_per_day",
    9: "cl_out_of_range_high",
    10: "cl_injection_limit",
    11: "cl_empty",
    12: "flow",
    13: "cl_out_of_range_low",
    14: "redox_high",
    15: "h2o2_out_of_range_high",
    16: "h2o2_injection_limit",
    17: "h2o2_sensor",
    18: "can_transmit",
    19: "low_water_level",
    20: "backfeed",
}
