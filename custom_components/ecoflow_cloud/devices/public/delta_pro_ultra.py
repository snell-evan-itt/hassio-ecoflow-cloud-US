from custom_components.ecoflow_cloud.api import EcoflowApiClient
from custom_components.ecoflow_cloud.devices import const, BaseDevice
from custom_components.ecoflow_cloud.entities import BaseSensorEntity, BaseNumberEntity, BaseSwitchEntity, \
    BaseSelectEntity, BaseButtonEntity
from custom_components.ecoflow_cloud.button import EnabledButtonEntity
from custom_components.ecoflow_cloud.switch import EnabledEntity
from custom_components.ecoflow_cloud.number import (
    ValueUpdateEntity, MaxBatteryLevelEntity, MinBatteryLevelEntity, ChargingPowerEntity,
)
from custom_components.ecoflow_cloud.sensor import (
    LevelSensorEntity, WattsSensorEntity, RemainSensorEntity,
    TempSensorEntity, CyclesSensorEntity, OutWattsSensorEntity,
    InWattsSensorEntity, VoltSensorEntity, AmpSensorEntity,
    CapacitySensorEntity, QuotaStatusSensorEntity, MiscSensorEntity,
    FrequencySensorEntity,
)
from homeassistant.const import UnitOfElectricCurrent


class PlainAmpSensorEntity(AmpSensorEntity):
    """AmpSensorEntity assumes raw integer milliamps (correct for several
    Private API fields), but the Public API's solar/AC-port current fields
    are already plain floats in Amps. Reusing AmpSensorEntity directly would
    silently mislabel a correct value as 1000x too small (e.g. a real 2.2A
    reading displaying as "2.2 mA") - this just swaps the unit, no math.

    _attr_suggested_unit_of_measurement must ALSO be set explicitly: without
    it, Home Assistant's own sensor component defaults to suggesting a
    smaller sub-unit (mA) for small Amp-scale readings regardless of the
    native unit declared above, which otherwise displays a value 1000x
    larger than native (e.g. "5421 mA" instead of "5.42 A") - mathematically
    consistent, but confusing and not what we actually want shown."""
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_suggested_unit_of_measurement = UnitOfElectricCurrent.AMPERE


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

            # ── Solar (MPPT) voltage / current - documented but previously missing ──
            VoltSensorEntity(client, self, "hs_yj751_pd_backend_addr.inHvMpptVol", "Solar HV In Voltage"),
            PlainAmpSensorEntity(client, self, "hs_yj751_pd_backend_addr.inHvMpptAmp", "Solar HV In Current"),
            VoltSensorEntity(client, self, "hs_yj751_pd_backend_addr.inLvMpptVol", "Solar LV In Voltage"),
            PlainAmpSensorEntity(client, self, "hs_yj751_pd_backend_addr.inLvMpptAmp", "Solar LV In Current"),

            # ── AC port voltage / current ───────────────────────────────────────
            VoltSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAc5p8Vol", "5.8kW Port Out Voltage"),
            PlainAmpSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAc5p8Amp", "5.8kW Port Out Current"),
            VoltSensorEntity(client, self, "hs_yj751_pd_backend_addr.inAc5p8Vol", "5.8kW Port In Voltage"),
            PlainAmpSensorEntity(client, self, "hs_yj751_pd_backend_addr.inAc5p8Amp", "5.8kW Port In Current"),
            VoltSensorEntity(client, self, "hs_yj751_pd_backend_addr.inAcC20Vol", "AC C20 In Voltage"),
            PlainAmpSensorEntity(client, self, "hs_yj751_pd_backend_addr.inAcC20Amp", "AC C20 In Current"),
            VoltSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAcL21Vol", "AC Out L2-1 Voltage"),
            PlainAmpSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAcL21Amp", "AC Out L2-1 Current"),
            VoltSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAcL22Vol", "AC Out L2-2 Voltage"),
            PlainAmpSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAcL22Amp", "AC Out L2-2 Current"),
            VoltSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAcL14Vol", "AC Out L1-4 Voltage"),
            PlainAmpSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAcL14Amp", "AC Out L1-4 Current"),
            VoltSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAcTtVol", "AC Out TT Voltage"),
            PlainAmpSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAcTtAmp", "AC Out TT Current"),
            PlainAmpSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAcL12Amp", "AC Out L1-2 Current"),

            # ── AC power factor (unitless, documented but no dedicated sensor class) ──
            MiscSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAcL11Pf", "AC Out L1-1 Power Factor"),
            MiscSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAcL12Pf", "AC Out L1-2 Power Factor"),
            MiscSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAcL21Pf", "AC Out L2-1 Power Factor"),
            MiscSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAcL22Pf", "AC Out L2-2 Power Factor"),
            MiscSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAcTtPf", "AC Out TT Power Factor"),
            MiscSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAcL14Pf", "AC Out L1-4 Power Factor"),
            MiscSensorEntity(client, self, "hs_yj751_pd_backend_addr.outAcP58Pf", "5.8kW Port Power Factor"),

            # ── Additional power readings documented but missing ───────────────
            OutWattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.outAcL14Pwr", "AC Out L1-4 Power"),
            OutWattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.outAdsPwr", "DC Anderson Out Power"),
            InWattsSensorEntity(client, self, "hs_yj751_pd_appshow_addr.inAcC20Pwr", "AC C20 In Power"),
            FrequencySensorEntity(client, self, "hs_yj751_pd_app_set_info_addr.acOutFreq", "AC Output Frequency"),

            # ── Savings Mode / Operating Mode - the settings behind the app's
            # confusing behavior, now visible as read-only sensors ────────────
            LevelSensorEntity(client, self, "hs_yj751_pd_app_set_info_addr.sysBackupSoc",
                              "Backup Reserve Level"),
            MiscSensorEntity(client, self, "hs_yj751_pd_app_set_info_addr.sysWordMode",
                             "Operating Mode (0=Default 1=Self-Powered 2=Scheduled 3=TOU)"),
            MiscSensorEntity(client, self, "hs_yj751_pd_app_set_info_addr.bmsModeSet",
                             "Battery Auto-Heat Enabled"),

            # ── Misc diagnostics ─────────────────────────────────────────────
            MiscSensorEntity(client, self, "hs_yj751_pd_appshow_addr.sysErrCode", "Error Code"),
            MiscSensorEntity(client, self, "hs_yj751_pd_appshow_addr.bpNum", "Battery Pack Count"),

            QuotaStatusSensorEntity(client, self),
        ]

    def numbers(self, client: EcoflowApiClient) -> list[BaseNumberEntity]:
        # All cmdCodes and params below are from EcoFlow's public API docs for this
        # device (YJ751_* prefix). None of these have been tested against real
        # hardware yet - go one at a time and verify before trusting the value.
        return [
            MaxBatteryLevelEntity(client, self, "hs_yj751_pd_app_set_info_addr.chgMaxSoc",
                                  "Max Charge Level", 50, 100,
                                  lambda value: {"cmdCode": "YJ751_PD_CHG_SOC_MAX_SET",
                                                 "params": {"maxChgSoc": int(value)}}),
            MinBatteryLevelEntity(client, self, "hs_yj751_pd_app_set_info_addr.dsgMinSoc",
                                  "Min Discharge Level", 0, 30,
                                  lambda value: {"cmdCode": "YJ751_PD_DSG_SOC_MIN_SET",
                                                 "params": {"minDsgSoc": int(value)}}),
            ValueUpdateEntity(client, self, "hs_yj751_pd_app_set_info_addr.powerStandbyMins",
                              "Device Standby Time (min)", 0, 1440,
                              lambda value: {"cmdCode": "YJ751_PD_POWER_STANDBY_SET",
                                             "params": {"powerStandbyMin": int(value)}}),
            ValueUpdateEntity(client, self, "hs_yj751_pd_app_set_info_addr.screenStandbySec",
                              "Screen Standby Time (sec)", 0, 3600,
                              lambda value: {"cmdCode": "YJ751_PD_SCREEN_STANDBY_SET",
                                             "params": {"screenStandbySec": int(value)}}),
            # The app itself refuses to apply this one while Savings Mode is on -
            # untested whether the public API enforces the same block.
            ValueUpdateEntity(client, self, "hs_yj751_pd_app_set_info_addr.acStandbyMins",
                              "AC Standby Time (min)", 0, 1440,
                              lambda value: {"cmdCode": "YJ751_PD_AC_STANDBY_SET",
                                             "params": {"acStandbyMin": int(value)}}),
            ValueUpdateEntity(client, self, "hs_yj751_pd_app_set_info_addr.dcStandbyMins",
                              "DC Standby Time (min)", 0, 1440,
                              lambda value: {"cmdCode": "YJ751_PD_DC_STANDBY_SET",
                                             "params": {"dcStandbyMin": int(value)}}),
            # Docs show both wattage fields sent together in one command - sending
            # only one here may reset the other to 0 on the device, untested.
            ChargingPowerEntity(client, self, "hs_yj751_pd_app_set_info_addr.chgC20SetWatts",
                                "AC C20 Charging Power", 200, 3000,
                                lambda value: {"cmdCode": "YJ751_PD_AC_CHG_SET",
                                               "params": {"chgC20Watts": int(value)}}),
            ChargingPowerEntity(client, self, "hs_yj751_pd_app_set_info_addr.chg5p8SetWatts",
                                "AC 5.8kW Port Charging Power", 200, 3900,
                                lambda value: {"cmdCode": "YJ751_PD_AC_CHG_SET",
                                               "params": {"chg5p8Watts": int(value)}}),
        ]

    def switches(self, client: EcoflowApiClient) -> list[BaseSwitchEntity]:
        return [
            EnabledEntity(client, self, "hs_yj751_pd_appshow_addr.wireless4gOn", "4G Modem",
                         lambda value: {"cmdCode": "YJ751_PD_4G_SWITCH_SET",
                                        "params": {"en4GOpen": value}}),
            EnabledEntity(client, self, "hs_yj751_pd_app_set_info_addr.acOftenOpenFlg", "AC Always-On",
                         lambda value: {"cmdCode": "YJ751_PD_AC_OFTEN_OPEN_SET",
                                        "params": {"acOftenOpen": value}}),
        ]

    def selects(self, client: EcoflowApiClient) -> list[BaseSelectEntity]:
        return []

    def buttons(self, client: EcoflowApiClient) -> list[BaseButtonEntity]:
        return [
            # AC output on/off via YJ751_PD_AC_DSG_SET, per EcoFlow's public API docs.
            # Buttons rather than a switch since the DPU's showFlag bitfield isn't
            # parsed yet for a reliable on/off read-back state.
            EnabledButtonEntity(client, self, "ac_output_off", "AC Output Off",
                                lambda value: {"cmdCode": "YJ751_PD_AC_DSG_SET",
                                               "params": {"enable": 0, "xboost": 1, "outFreq": 60}}),
            EnabledButtonEntity(client, self, "ac_output_on", "AC Output On",
                                lambda value: {"cmdCode": "YJ751_PD_AC_DSG_SET",
                                               "params": {"enable": 1, "xboost": 1, "outFreq": 60}}),
            # No documented readback field for this one (showFlag bitfield again),
            # so a button pair rather than a switch, same as AC output above.
            EnabledButtonEntity(client, self, "battery_heat_on", "Battery Heating On",
                                lambda value: {"cmdCode": "YJ751_PD_BP_HEAT_SET",
                                               "params": {"enBpHeat": 1}}),
            EnabledButtonEntity(client, self, "battery_heat_off", "Battery Heating Off",
                                lambda value: {"cmdCode": "YJ751_PD_BP_HEAT_SET",
                                               "params": {"enBpHeat": 0}}),
            EnabledButtonEntity(client, self, "dc_output_on", "DC Output On",
                                lambda value: {"cmdCode": "YJ751_PD_DC_SWITCH_SET",
                                               "params": {"enable": 1}}),
            EnabledButtonEntity(client, self, "dc_output_off", "DC Output Off",
                                lambda value: {"cmdCode": "YJ751_PD_DC_SWITCH_SET",
                                               "params": {"enable": 0}}),
        ]
