"""High level orchestration service implementing complex domain actions."""
from __future__ import annotations

import collections
import logging
import time
from typing import Dict, Iterable, List, Optional

from ..middleware.broker import InteractionBroker
from ..middleware.exceptions import EnvironmentFault, SutFault
from .precondition_service import PreconditionService


class DomainService:
    """Encapsulate macro interactions spanning multiple subsystems."""

    def __init__(
        self,
        broker: InteractionBroker,
        preconditions: PreconditionService,
        logger: logging.Logger,
    ) -> None:
        self._broker = broker
        self._preconditions = preconditions
        self._logger = logger
        self._captures: Dict[str, float] = {}
        self._backend_commands: Dict[str, str] = {}
        self._dtc_store: Dict[str, List[str]] = collections.defaultdict(list)

    # ------------------------------------------------------------------
    # Global, cross-cutting actions
    # ------------------------------------------------------------------
    def set_ignition_state(self, state: str) -> None:
        self._logger.info("Setting ignition state to %s", state)
        self._broker.set_signal("VehicleIgnitionStatus", state)
        self._broker.wait_for_signal("VehicleIgnitionStatus", state, timeout_s=5)

    def set_signal(self, signal: str, value) -> None:
        self._broker.set_signal(signal, value)

    def wait_for_signal(self, signal: str, value, timeout_s: float = 5.0) -> None:
        self._broker.wait_for_signal(signal, value, timeout_s=timeout_s)

    def get_signal(self, signal: str, timeout_s: float = 1.0):
        return self._broker.get_signal(signal, timeout_s=timeout_s)

    def set_operating_mode(self, mode: str) -> None:
        self._logger.info("Setting operating mode to %s", mode)
        self._broker.set_signal("VehicleOperatingMode", mode)
        self._broker.wait_for_signal("VehicleOperatingMode", mode, timeout_s=5)

    def ensure_precondition(self, name: str) -> None:
        self._logger.info("Ensuring precondition %s", name)
        self._preconditions.apply(name)

    def apply_epb(self, state: str) -> None:
        self._logger.info("Commanding EPB state %s", state)
        self._broker.set_signal("EPBCommand", state)
        self._broker.wait_for_signal("EPBStatus", state, timeout_s=5)

    def set_gear(self, gear: str) -> None:
        self._logger.info("Selecting gear %s", gear)
        self._broker.set_signal("GearCommand", gear)
        self._broker.wait_for_signal("GearPosition", gear, timeout_s=5)

    def set_vehicle_speed(self, speed: float) -> None:
        speed_value = float(speed)
        self._logger.info("Setting vehicle speed to %.1f km/h", speed_value)
        self._broker.set_signal("VehicleSpeedTarget", int(speed_value))
        self._broker.assert_signal_in_range("VehicleSpeed", 0.0, max(speed_value, 1.0))

    def force_backend_action(self, command: str) -> None:
        normalized = command.upper().replace(" ", "_")
        self._logger.info("Issuing backend command %s", normalized)
        self._backend_commands[normalized] = "PENDING"
        self._broker.set_signal("BackendCommandRequest", normalized)

    def wait_backend_ack(self, command: str, expected: str) -> None:
        normalized = command.upper().replace(" ", "_")
        self._logger.info("Waiting for backend ack %s -> %s", normalized, expected)
        self._broker.wait_for_signal("BackendCommandAck", expected.upper(), timeout_s=10)
        self._backend_commands[normalized] = expected.upper()

    def assert_backend_consistency(self, signals: Iterable[str]) -> None:
        self._broker.assert_consistent_signals(signals, timeout_s=5)

    def verify_no_comm_faults(self) -> None:
        self._broker.assert_no_faults(["BusFaultStatus", "SomeIpFaultStatus"], timeout_s=5)

    def start_capture(self, channel: str) -> None:
        if channel in self._captures:
            raise EnvironmentFault(f"Capture for {channel} already running")
        self._logger.info("Starting capture for %s", channel)
        self._captures[channel] = time.time()

    def stop_capture(self, channel: str) -> float:
        if channel not in self._captures:
            raise EnvironmentFault(f"Capture for {channel} was not started")
        start = self._captures.pop(channel)
        duration = time.time() - start
        self._logger.info("Stopped capture %s after %.2fs", channel, duration)
        return duration

    def snapshot_state(self, label: str) -> None:
        self._logger.info("Taking evidence snapshot: %s", label)

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------
    def read_dtc(self, ecu: str) -> List[str]:
        self._logger.info("Reading DTCs for %s", ecu)
        return list(self._dtc_store[ecu])

    def clear_dtc(self, ecu: Optional[str] = None) -> None:
        if ecu:
            self._logger.info("Clearing DTCs for %s", ecu)
            self._dtc_store[ecu].clear()
        else:
            self._logger.info("Clearing DTCs for all ECUs")
            for codes in self._dtc_store.values():
                codes.clear()
        self._broker.set_signal("ActiveDtcCount", 0)

    def verify_no_active_dtc(self, ecu: Optional[str] = None) -> None:
        if ecu and self._dtc_store[ecu]:
            raise SutFault(f"ECU {ecu} still reports DTCs: {self._dtc_store[ecu]}")
        if not ecu:
            for name, codes in self._dtc_store.items():
                if codes:
                    raise SutFault(f"ECU {name} still reports DTCs: {codes}")
        self._broker.assert_signal_equal("ActiveDtcCount", 0, timeout_s=2)

    # ------------------------------------------------------------------
    # RTCU / telematics
    # ------------------------------------------------------------------
    def trigger_ecall(self) -> None:
        self._logger.info("Triggering eCall scenario")
        self._broker.set_signal("ECallScenario", "ACTIVE")

    def cancel_ecall(self) -> None:
        self._logger.info("Cancelling eCall scenario")
        self._broker.set_signal("ECallScenario", "INACTIVE")

    def verify_emergency_led(self, expected: str) -> None:
        self._broker.assert_signal_equal("EmergencyLedStatus", expected.upper(), timeout_s=5)

    def verify_psap_session(self, expected_active: bool) -> None:
        target = "CONNECTED" if expected_active else "DISCONNECTED"
        self._broker.assert_signal_equal("PsapSessionStatus", target, timeout_s=5)

    # ------------------------------------------------------------------
    # HMI / SOME-IP
    # ------------------------------------------------------------------
    def hmi_press(self, control: str) -> None:
        self._logger.info("Pressing HMI control %s", control)
        self._broker.set_signal("HMICommand", control.upper())

    def hmi_navigate(self, path: str) -> None:
        self._logger.info("Navigating HMI path %s", path)
        self._broker.set_signal("HMINavigationState", path.upper())

    def expect_telltale(self, name: str, state: str) -> None:
        signal = f"ClusterTelltale{name.replace(' ', '')}"
        self._broker.assert_signal_equal(signal, state.upper(), timeout_s=5)

    def hmi_open_app(self, app: str) -> None:
        self._logger.info("Opening HMI app %s", app)
        self._broker.set_signal("HMIActiveApp", app.upper())

    def hmi_select(self, option_path: str) -> None:
        self._logger.info("Selecting HMI option %s", option_path)
        self._broker.set_signal("HMISelection", option_path.upper())

    def wait_someip_field(self, path: str, value: str, timeout_s: float = 5.0) -> None:
        signal = self._normalize_someip_path(path)
        self._broker.wait_for_signal(signal, value.upper(), timeout_s=timeout_s)

    def _normalize_someip_path(self, path: str) -> str:
        normalized = path.replace(".", "_").replace("/", "_").upper()
        return f"SOMEIP::{normalized}"

    # ------------------------------------------------------------------
    # Brain / wired I/O
    # ------------------------------------------------------------------
    def set_securement_state(self, state: str) -> None:
        self._broker.set_signal("SecurementState", state.upper())
        self._broker.wait_for_signal("SecurementState", state.upper(), timeout_s=5)

    def verify_securement_state(self, state: str) -> None:
        self._broker.assert_signal_equal("SecurementState", state.upper(), timeout_s=5)

    def wired_set(self, name: str, value) -> None:
        signal = f"WIRED::{name.upper()}"
        self._broker.set_signal(signal, value)

    def verify_wired_output(self, name: str, value) -> None:
        signal = f"WIRED::{name.upper()}"
        self._broker.assert_signal_equal(signal, value, timeout_s=5)

    def verify_bus_signal(self, name: str, value) -> None:
        self._broker.assert_signal_equal(name, value, timeout_s=5)

    # ------------------------------------------------------------------
    # Zonal domains
    # ------------------------------------------------------------------
    def set_front_door(self, door: str, state: str) -> None:
        signal = f"Door{door.upper()}State"
        self._broker.set_signal(signal, state.upper())
        self._broker.wait_for_signal(signal, state.upper(), timeout_s=5)

    def verify_door_state(self, door: str, state: str) -> None:
        signal = f"Door{door.upper()}State"
        self._broker.assert_signal_equal(signal, state.upper(), timeout_s=5)

    def set_low_beam(self, state: str) -> None:
        self._broker.set_signal("LowBeamCommand", state.upper())
        self._broker.wait_for_signal("LowBeamState", state.upper(), timeout_s=5)

    def verify_low_beam(self, state: str) -> None:
        self._broker.assert_signal_equal("LowBeamState", state.upper(), timeout_s=5)

    def set_seatbelt(self, seat: str, state: str) -> None:
        signal = f"Seatbelt{seat.upper()}State"
        self._broker.set_signal(signal, state.upper())
        self._broker.wait_for_signal(signal, state.upper(), timeout_s=5)

    def command_window(self, door: str, command: str) -> None:
        signal = f"Window{door.upper()}Command"
        self._broker.set_signal(signal, command.upper())

    def verify_window_position(self, door: str, state: str) -> None:
        signal = f"Window{door.upper()}Position"
        self._broker.assert_signal_equal(signal, state.upper(), timeout_s=5)

    def set_hvac_temperature(self, temperature: float) -> None:
        self._broker.set_signal("HVACTemperature", int(temperature))
        self._broker.assert_signal_in_range("HVACTemperature", temperature - 1, temperature + 1)

    def verify_hvac_mode(self, mode: str) -> None:
        self._broker.assert_signal_equal("HVACMode", mode.upper(), timeout_s=5)

    def enable_demist(self) -> None:
        self._broker.set_signal("HVACDemistCommand", "ON")

    def verify_defrost(self, state: str) -> None:
        self._broker.assert_signal_equal("DefrostStatus", state.upper(), timeout_s=5)

    # ------------------------------------------------------------------
    # ADAS
    # ------------------------------------------------------------------
    def adas_enable(self, feature: str) -> None:
        signal = f"ADAS{feature.upper()}State"
        self._broker.set_signal(signal, "ENABLED")

    def adas_disable(self, feature: str) -> None:
        signal = f"ADAS{feature.upper()}State"
        self._broker.set_signal(signal, "DISABLED")

    def adas_set_speed(self, speed: float) -> None:
        self._broker.set_signal("ADASpeedSetpoint", int(speed))
        self._broker.wait_for_signal("ADASpeedSetpoint", int(speed), timeout_s=5)

    def adas_inject_obstacle(self, distance: float) -> None:
        self._broker.set_signal("ADASObstacleDistance", int(distance))

    def verify_wpp_control_request(self, request: str) -> None:
        self._broker.assert_signal_equal("WPPControlRequest", request.upper(), timeout_s=5)

    # ------------------------------------------------------------------
    # Energy / Charging
    # ------------------------------------------------------------------
    def connect_evse(self) -> None:
        self._broker.set_signal("ChargingState", "CONNECTED")

    def disconnect_evse(self) -> None:
        self._broker.set_signal("ChargingState", "DISCONNECTED")

    def verify_charging_active(self, expected: bool) -> None:
        value = "ACTIVE" if expected else "INACTIVE"
        self._broker.assert_signal_equal("ChargingActivity", value, timeout_s=5)

    # ------------------------------------------------------------------
    # Brake / vehicle securement
    # ------------------------------------------------------------------
    def press_brake(self) -> None:
        self._broker.set_signal("BrakePedalStatus", "PRESSED")

    def release_brake(self) -> None:
        self._broker.set_signal("BrakePedalStatus", "RELEASED")

    def verify_brake_telltale(self, state: str) -> None:
        self._broker.assert_signal_equal("ClusterBrakeTelltale", state.upper(), timeout_s=5)

    # ------------------------------------------------------------------
    # Lighting / environment
    # ------------------------------------------------------------------
    def set_high_beam(self, state: str) -> None:
        self._broker.set_signal("HighBeamCommand", state.upper())
        self._broker.wait_for_signal("HighBeamState", state.upper(), timeout_s=5)

    def flash_to_pass(self) -> None:
        self._broker.set_signal("HighBeamCommand", "FLASH")

    def verify_light_availability(self, name: str, state: str) -> None:
        signal = f"LightAvailability{name.replace(' ', '')}"
        self._broker.assert_signal_equal(signal, state.upper(), timeout_s=5)

    # ------------------------------------------------------------------
    # Wipers / washers
    # ------------------------------------------------------------------
    def set_wiper_mode(self, mode: str) -> None:
        self._broker.set_signal("WiperRequest", mode.upper())

    def spray_washer(self) -> None:
        self._broker.set_signal("WiperWasherCommand", "SPRAY")

    def verify_wipers_state(self, state: str) -> None:
        self._broker.assert_signal_equal("WiperMotorStatus", state.upper(), timeout_s=5)

    # ------------------------------------------------------------------
    # Access control
    # ------------------------------------------------------------------
    def lock_vehicle(self) -> None:
        self._broker.set_signal("VehicleLockState", "LOCKED")

    def unlock_vehicle(self) -> None:
        self._broker.set_signal("VehicleLockState", "UNLOCKED")

    def open_luggage(self) -> None:
        self._broker.set_signal("LuggageState", "OPEN")

    def verify_luggage_state(self, state: str) -> None:
        self._broker.assert_signal_equal("LuggageState", state.upper(), timeout_s=5)

    # ------------------------------------------------------------------
    # Speed / pace management
    # ------------------------------------------------------------------
    def enable_speed_limiter(self) -> None:
        self._broker.set_signal("SpeedLimiterStatus", "ENABLED")

    def set_speed_limit(self, value: float) -> None:
        self._broker.set_signal("SpeedLimiterValue", int(value))

    def verify_speed_limit_status(self, status: str) -> None:
        self._broker.assert_signal_equal("SpeedLimiterStatus", status.upper(), timeout_s=5)

    # ------------------------------------------------------------------
    # ECU health
    # ------------------------------------------------------------------
    def ecu_ping(self, ecu: str) -> None:
        self._logger.info("Pinging ECU %s", ecu)
        self._broker.set_signal("EcuHeartbeat", ecu.upper())


__all__ = ["DomainService"]
