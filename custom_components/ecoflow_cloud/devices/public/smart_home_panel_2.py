from typing import Any

import jsonpath_ng.ext as jp

from custom_components.ecoflow_cloud.api import EcoflowApiClient
from custom_components.ecoflow_cloud.devices import const, BaseDevice
from custom_components.ecoflow_cloud.entities import BaseSensorEntity, BaseNumberEntity, BaseSwitchEntity, \
    BaseSelectEntity
from custom_components.ecoflow_cloud.sensor import (
    LevelSensorEntity, WattsSensorEntity, RemainSensorEntity,
    VoltSensorEntity, FrequencySensorEntity, MiscSensorEntity,
    QuotaStatusSensorEntity,
)


class CircuitWattsSensorEntity(WattsSensorEntity):
    """Reads one element from an array-valued quota key.

    The EcoFlow Smart Home Panel 2 reports per-circuit watts as a single
    JSON array key (e.g. ``loadInfo.hall1Watt`` = [w1, w2, ..., w12]).
    This entity wraps that array key and exposes a single indexed element,
    generating a unique entity ID from ``<array_key>.<index>``.
    """

    def __init__(self, client: EcoflowApiClient, device: BaseDevice,
                 array_key: str, index: int, title: str, enabled: bool = True):
        # Parent stores <array_key>.<index> as the mqtt_key → unique entity ID
        super().__init__(client, device, f"{array_key}.{index}", title, enabled)
        # Override lookup to fetch the whole array under the real flat key
        self._mqtt_key_adopted = "'" + array_key + "'"
        self._mqtt_key_expr = jp.parse(self._mqtt_key_adopted)
        self._index = index

    def _update_value(self, val: Any) -> bool:
        if isinstance(val, list) and len(val) > self._index:
            return super()._update_value(val[self._index])
        return False


class SmartHomePanel2(BaseDevice):
    """EcoFlow Smart Home Panel 2 – public API device.

    Key structure in the quota response:
      wattInfo.*                              – whole-panel power summary
      loadInfo.hall1Watt                      – array[12] of per-circuit watts
      pd303_mc.masterIncreInfo.*              – grid voltage / relay state
      pd303_mc.backupIncreInfo.*              – backup battery & channel info
      pd303_mc.loadIncreInfo.hall1IncreInfo.* – per-circuit names, limits, state
      backupInfo.*                            – backup timing
    """

    def sensors(self, client: EcoflowApiClient) -> list[BaseSensorEntity]:
        return [
            # ── Whole-panel power ────────────────────────────────────────────────
            WattsSensorEntity(client, self, "wattInfo.gridWatt", "Grid Power"),
            WattsSensorEntity(client, self, "wattInfo.allHallWatt", "Total Load Power"),

            # ── Per-circuit watts (12-element array, 0-indexed) ──────────────────
            # Indices correspond to circuits 1-12 as labelled in the EcoFlow app.
            CircuitWattsSensorEntity(client, self, "loadInfo.hall1Watt", 0, "Circuit 1 Power"),
            CircuitWattsSensorEntity(client, self, "loadInfo.hall1Watt", 1, "Circuit 2 Power"),
            CircuitWattsSensorEntity(client, self, "loadInfo.hall1Watt", 2, "Circuit 3 Power"),
            CircuitWattsSensorEntity(client, self, "loadInfo.hall1Watt", 3, "Circuit 4 Power"),
            CircuitWattsSensorEntity(client, self, "loadInfo.hall1Watt", 4, "Circuit 5 Power"),
            CircuitWattsSensorEntity(client, self, "loadInfo.hall1Watt", 5, "Circuit 6 Power"),
            CircuitWattsSensorEntity(client, self, "loadInfo.hall1Watt", 6, "Circuit 7 Power"),
            CircuitWattsSensorEntity(client, self, "loadInfo.hall1Watt", 7, "Circuit 8 Power"),
            CircuitWattsSensorEntity(client, self, "loadInfo.hall1Watt", 8, "Circuit 9 Power"),
            CircuitWattsSensorEntity(client, self, "loadInfo.hall1Watt", 9, "Circuit 10 Power"),
            CircuitWattsSensorEntity(client, self, "loadInfo.hall1Watt", 10, "Circuit 11 Power"),
            CircuitWattsSensorEntity(client, self, "loadInfo.hall1Watt", 11, "Circuit 12 Power"),

            # ── Backup battery (connected unit, e.g. DELTA Pro Ultra) ─────────────
            LevelSensorEntity(client, self, "pd303_mc.backupIncreInfo.backupBatPer",
                              "Backup Battery Level")
            .attr("pd303_mc.backupIncreInfo.backupFullCap", "Full Capacity (Wh)", 0)
            .attr("pd303_mc.backupIncreInfo.backupDischargeRmainBatCap", "Remain Capacity (Wh)", 0),

            # Battery percentage as reported directly by the connected backup device
            LevelSensorEntity(client, self,
                              "pd303_mc.backupIncreInfo.Energy3Info.batteryPercentage",
                              "Backup Unit Battery Level", False),
            WattsSensorEntity(client, self,
                              "pd303_mc.backupIncreInfo.Energy3Info.outputPower",
                              "Backup Unit Output Power", False),

            # ── Backup channel watts (3-element array, 0-indexed) ─────────────────
            CircuitWattsSensorEntity(client, self, "wattInfo.chWatt", 0,
                                     "Backup Channel 1 Power", False),
            CircuitWattsSensorEntity(client, self, "wattInfo.chWatt", 1,
                                     "Backup Channel 2 Power", False),
            CircuitWattsSensorEntity(client, self, "wattInfo.chWatt", 2,
                                     "Backup Channel 3 Power", False),

            # ── Grid ──────────────────────────────────────────────────────────────
            VoltSensorEntity(client, self, "pd303_mc.masterIncreInfo.gridVol", "Grid Voltage"),
            FrequencySensorEntity(client, self, "pd303_mc.gridFreq", "Grid Frequency"),

            # ── Backup timing ────────────────────────────────────────────────────
            RemainSensorEntity(client, self, "backupInfo.backupChargeTime",
                               const.CHARGE_REMAINING_TIME),
            RemainSensorEntity(client, self, "backupInfo.backupDischargeTime",
                               const.DISCHARGE_REMAINING_TIME),

            # ── Operating state & config ──────────────────────────────────────────
            LevelSensorEntity(client, self, "pd303_mc.backupReserveSoc",
                              "Backup Reserve Level", False),
            WattsSensorEntity(client, self, "pd303_mc.chargeWattPower", "Charge Power", False),
            MiscSensorEntity(client, self, "pd303_mc.powerSta", "Power Status", False),
            MiscSensorEntity(client, self, "pd303_mc.backupIncreInfo.ch3Info.ctrlSta",
                             "Backup Channel 3 Status", False),
            MiscSensorEntity(client, self, "pd303_mc.sysCurRunningState",
                             "System Running State", False),

            QuotaStatusSensorEntity(client, self),
        ]

    def numbers(self, client: EcoflowApiClient) -> list[BaseNumberEntity]:
        # Write command formats for Smart Home Panel 2 public API not yet known.
        return []

    def switches(self, client: EcoflowApiClient) -> list[BaseSwitchEntity]:
        return []

    def selects(self, client: EcoflowApiClient) -> list[BaseSelectEntity]:
        return []
