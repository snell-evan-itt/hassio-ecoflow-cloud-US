from custom_components.ecoflow_cloud.api import EcoflowApiClient
from custom_components.ecoflow_cloud.devices import const, BaseDevice
from custom_components.ecoflow_cloud.entities import BaseSensorEntity, BaseNumberEntity, BaseSwitchEntity, \
    BaseSelectEntity
from custom_components.ecoflow_cloud.sensor import (
    LevelSensorEntity, WattsSensorEntity, RemainSensorEntity,
    TempSensorEntity, CyclesSensorEntity, OutWattsSensorEntity,
    InWattsSensorEntity, VoltSensorEntity, AmpSensorEntity,
    CapacitySensorEntity, QuotaStatusSensorEntity,
)


class DeltaProUltra(BaseDevice):
    """EcoFlow DELTA Pro Ultra – public API device.

    Key prefixes in the quota response:
      hs_yj751_pd_appshow_addr.*   – display/summary values (SOC, watts in/out, etc.)
      hs_yj751_pd_backend_addr.*   – inverter/BMS backend values (volts, temps, etc.)
      hs_yj751_bms_slave_addr.N.*  – per-pack BMS data (N = 1 or 2)
      hs_yj751_pd_app_set_info_addr.* – user-configurable settings
    """

    def sensors(self, client: EcoflowApiClient) -> list[BaseSensorEntity]:
        return [
            # ── Main battery level ──────────────────────────────────────────────
            LevelSensorEntity(client, self, "hs_yj751_pd_appshow_addr.soc", const.MAIN_BATTERY_LEVEL)
            .attr("hs_yj751_bms_slave_addr.1.remainCap", const.ATTR_REMAIN_CAPACITY, 0)
            .attr("hs_yj751_bms_slave_addr.1.fullCap", const.ATTR_FULL_CAPACITY, 0)
            .attr("hs_yj751_bms_slave_addr.1.designCap", const.ATTR_DESIGN_CAPACITY, 0),

            # ── Total power (in / out) ──────────────────────────────────────────
            WattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.wattsInSum", const.TOTAL_IN_POWER),
            WattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.wattsOutSum", const.TOTAL_OUT_POWER),

            # ── Discharge remaining time ────────────────────────────────────────
            RemainSensorEntity(client, self, "hs_yj751_pd_appshow_addr.remainTime",
                               const.DISCHARGE_REMAINING_TIME),

            # ── AC ports ────────────────────────────────────────────────────────
            # 5.8 kW AC input port
            InWattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.inAc5p8Pwr", const.AC_IN_POWER),
            # AC output – total and per-leg
            OutWattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.outAcTtPwr", const.AC_OUT_POWER),
            OutWattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.outAcL11Pwr", "AC Out L1-1 Power"),
            OutWattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.outAcL12Pwr", "AC Out L1-2 Power"),
            OutWattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.outAcL21Pwr", "AC Out L2-1 Power"),
            OutWattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.outAcL22Pwr", "AC Out L2-2 Power"),
            OutWattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.outAc5p8Pwr", "5.8kW Port Out Power"),

            # ── Solar (MPPT) ────────────────────────────────────────────────────
            InWattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.inHvMpptPwr", "Solar HV In Power"),
            InWattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.inLvMpptPwr", "Solar LV In Power"),

            # ── USB / Type-C ────────────────────────────────────────────────────
            OutWattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.outTypec1Pwr",
                                 const.TYPEC_1_OUT_POWER),
            OutWattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.outTypec2Pwr",
                                 const.TYPEC_2_OUT_POWER),
            OutWattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.outUsb1Pwr", const.USB_1_OUT_POWER),
            OutWattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.outUsb2Pwr", const.USB_2_OUT_POWER),

            # ── BMS backend ────────────────────────────────────────────────────
            WattsSensorEntity(client, self, "hs_yj751_pd_backend_addr.bmsOutputWatts", "BMS Output Power"),
            WattsSensorEntity(client, self, "hs_yj751_pd_backend_addr.bmsInputWatts", "BMS Input Power"),
            VoltSensorEntity(client, self, "hs_yj751_pd_backend_addr.batVol", const.BATTERY_VOLT, False),

            # ── Temperatures ────────────────────────────────────────────────────
            TempSensorEntity(client, self, "hs_yj751_pd_backend_addr.pcsAcTemp", "PCS Temperature"),
            TempSensorEntity(client, self, "hs_yj751_pd_backend_addr.pdTemp", "PD Temperature"),

            # ── Battery Pack 1 (hs_yj751_bms_slave_addr.1.*) ───────────────────
            LevelSensorEntity(client, self, "hs_yj751_bms_slave_addr.1.soc",
                              const.SLAVE_N_BATTERY_LEVEL % 1, False, True)
            .attr("hs_yj751_bms_slave_addr.1.remainCap", const.ATTR_REMAIN_CAPACITY, 0)
            .attr("hs_yj751_bms_slave_addr.1.fullCap", const.ATTR_FULL_CAPACITY, 0)
            .attr("hs_yj751_bms_slave_addr.1.designCap", const.ATTR_DESIGN_CAPACITY, 0),
            CapacitySensorEntity(client, self, "hs_yj751_bms_slave_addr.1.remainCap",
                                 const.SLAVE_N_REMAIN_CAPACITY % 1, False),
            CapacitySensorEntity(client, self, "hs_yj751_bms_slave_addr.1.fullCap",
                                 const.SLAVE_N_FULL_CAPACITY % 1, False),
            CapacitySensorEntity(client, self, "hs_yj751_bms_slave_addr.1.designCap",
                                 const.SLAVE_N_DESIGN_CAPACITY % 1, False),
            TempSensorEntity(client, self, "hs_yj751_bms_slave_addr.1.temp",
                             const.SLAVE_N_BATTERY_TEMP % 1, False, True),
            CyclesSensorEntity(client, self, "hs_yj751_bms_slave_addr.1.cycles",
                               const.SLAVE_N_CYCLES % 1, False),
            AmpSensorEntity(client, self, "hs_yj751_bms_slave_addr.1.amp",
                            const.SLAVE_N_BATTERY_CURRENT % 1, False),

            # ── Battery Pack 2 (hs_yj751_bms_slave_addr.2.*) ───────────────────
            LevelSensorEntity(client, self, "hs_yj751_bms_slave_addr.2.soc",
                              const.SLAVE_N_BATTERY_LEVEL % 2, False, True)
            .attr("hs_yj751_bms_slave_addr.2.remainCap", const.ATTR_REMAIN_CAPACITY, 0)
            .attr("hs_yj751_bms_slave_addr.2.fullCap", const.ATTR_FULL_CAPACITY, 0)
            .attr("hs_yj751_bms_slave_addr.2.designCap", const.ATTR_DESIGN_CAPACITY, 0),
            CapacitySensorEntity(client, self, "hs_yj751_bms_slave_addr.2.remainCap",
                                 const.SLAVE_N_REMAIN_CAPACITY % 2, False),
            CapacitySensorEntity(client, self, "hs_yj751_bms_slave_addr.2.fullCap",
                                 const.SLAVE_N_FULL_CAPACITY % 2, False),
            CapacitySensorEntity(client, self, "hs_yj751_bms_slave_addr.2.designCap",
                                 const.SLAVE_N_DESIGN_CAPACITY % 2, False),
            TempSensorEntity(client, self, "hs_yj751_bms_slave_addr.2.temp",
                             const.SLAVE_N_BATTERY_TEMP % 2, False, True),
            CyclesSensorEntity(client, self, "hs_yj751_bms_slave_addr.2.cycles",
                               const.SLAVE_N_CYCLES % 2, False),
            AmpSensorEntity(client, self, "hs_yj751_bms_slave_addr.2.amp",
                            const.SLAVE_N_BATTERY_CURRENT % 2, False),

            QuotaStatusSensorEntity(client, self),
        ]

    def numbers(self, client: EcoflowApiClient) -> list[BaseNumberEntity]:
        # Write command formats for DPU public API not yet known.
        return []

    def switches(self, client: EcoflowApiClient) -> list[BaseSwitchEntity]:
        return []

    def selects(self, client: EcoflowApiClient) -> list[BaseSelectEntity]:
        return []
