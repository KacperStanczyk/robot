"""Robot Framework keywords that expose complex domain flows."""
from __future__ import annotations

from typing import Iterable, List, Sequence

from robot.api.deco import keyword

from ..services.domain_service import DomainService


class DomainKeywords:
    """Expose orchestration heavy keywords backed by :class:`DomainService`."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self, domain: DomainService):
        self._domain = domain

    # ------------------------------------------------------------------
    # Global macros and helpers
    # ------------------------------------------------------------------
    @keyword("PRECOND.Ensure Standby")
    def ensure_standby(self) -> None:
        self._domain.ensure_precondition("Standby")

    @keyword("PRECOND.Ensure In Use")
    def ensure_in_use(self) -> None:
        self._domain.ensure_precondition("InUse")

    @keyword("PRECOND.Ensure Driving")
    def ensure_driving(self) -> None:
        self._domain.ensure_precondition("Driving")

    @keyword("PRECOND.Ensure Charging")
    def ensure_charging(self) -> None:
        self._domain.ensure_precondition("Charging")

    @keyword("PRECOND.Ensure HVAC Base")
    def ensure_hvac_base(self) -> None:
        self._domain.ensure_precondition("HVACBase")

    @keyword("PRECOND.Ensure Lighting Base")
    def ensure_lighting_base(self) -> None:
        self._domain.ensure_precondition("LightingBase")

    @keyword("BUS.Get Signal")
    def bus_get_signal(self, signal: str, timeout: float = 1.0):
        return self._domain.get_signal(signal, timeout_s=float(timeout))

    @keyword("BACKEND.Send Command")
    def backend_send_command(self, command: str) -> None:
        self._domain.force_backend_action(command)

    @keyword("BACKEND.Wait For Ack")
    def backend_wait_for_ack(self, command: str, expected: str = "ACKED") -> None:
        self._domain.wait_backend_ack(command, expected)

    @keyword("BACKEND.Assert Vehicle Consistency")
    def backend_assert_vehicle_consistency(self, *signals: str) -> None:
        resolved = self._normalize_signals(signals)
        self._domain.assert_backend_consistency(resolved)

    @keyword("CAPTURE.Start")
    def capture_start(self, channel: str) -> None:
        self._domain.start_capture(channel)

    @keyword("CAPTURE.Stop")
    def capture_stop(self, channel: str) -> float:
        return self._domain.stop_capture(channel)

    @keyword("EVIDENCE.Snapshot")
    def evidence_snapshot(self, label: str) -> None:
        self._domain.snapshot_state(label)

    @keyword("DIAG.Read DTC")
    def diag_read_dtc(self, ecu: str) -> List[str]:
        return self._domain.read_dtc(ecu)

    @keyword("DIAG.Clear DTC")
    def diag_clear_dtc(self, ecu: str = "") -> None:
        target = ecu or None
        self._domain.clear_dtc(target)

    @keyword("DIAG.Verify No Active DTC")
    def diag_verify_no_active_dtc(self, ecu: str = "") -> None:
        target = ecu or None
        self._domain.verify_no_active_dtc(target)

    @keyword("VERIFY.No Active DTCs ECU")
    def verify_no_active_dtcs_ecu(self, ecu: str = "") -> None:
        self.diag_verify_no_active_dtc(ecu)

    @keyword("VERIFY.No Communication Faults")
    def verify_no_comm_faults(self) -> None:
        self._domain.verify_no_comm_faults()

    # ------------------------------------------------------------------
    # RTCU / telematics
    # ------------------------------------------------------------------
    @keyword("RTCU.Trigger ECall")
    def rtcu_trigger_ecall(self) -> None:
        self._domain.trigger_ecall()

    @keyword("RTCU.Cancel ECall")
    def rtcu_cancel_ecall(self) -> None:
        self._domain.cancel_ecall()

    @keyword("BACKEND.Send Remote Lock")
    def backend_send_remote_lock(self) -> None:
        self._domain.force_backend_action("REMOTE_LOCK")

    @keyword("BACKEND.Wait Ack")
    def backend_wait_ack(self, expected: str = "ACKED") -> None:
        self._domain.wait_backend_ack("REMOTE_LOCK", expected)

    @keyword("VERIFY.Emergency LED ==")
    def verify_emergency_led(self, expected: str) -> None:
        self._domain.verify_emergency_led(expected)

    @keyword("VERIFY.PSAP Session Established ==")
    def verify_psap_session(self, state: str) -> None:
        self._domain.verify_psap_session(state.strip().upper() in {"TRUE", "1", "YES"})

    # ------------------------------------------------------------------
    # SOME-IP / cluster
    # ------------------------------------------------------------------
    @keyword("SOMEIP.Wait Field")
    def someip_wait_field(self, path: str, value: str, timeout: float = 5.0) -> None:
        self._domain.wait_someip_field(path, value, timeout_s=float(timeout))

    @keyword("VERIFY.Cluster Telltale ==")
    def verify_cluster_telltale(self, name: str, state: str) -> None:
        self._domain.expect_telltale(name, state)

    # ------------------------------------------------------------------
    # Brain / wired
    # ------------------------------------------------------------------
    @keyword("BRAIN.Set Securement State =")
    def brain_set_securement(self, state: str) -> None:
        self._domain.set_securement_state(state)

    @keyword("VERIFY.Securement State ==")
    def verify_securement_state(self, state: str) -> None:
        self._domain.verify_securement_state(state)

    @keyword("WIRED.Set")
    def wired_set(self, name: str, value) -> None:
        self._domain.wired_set(name, value)

    @keyword("VERIFY.WIRED Output ==")
    def verify_wired_output(self, name: str, value) -> None:
        self._domain.verify_wired_output(name, value)

    @keyword("BUS.Verify Signal ==")
    def bus_verify_signal(self, signal: str, value) -> None:
        self._domain.verify_bus_signal(signal, value)

    # ------------------------------------------------------------------
    # Zonal domains
    # ------------------------------------------------------------------
    @keyword("ZONAL.FRONT.Set Door =")
    def zonal_front_set_door(self, door: str, state: str) -> None:
        self._domain.set_front_door(door, state)

    @keyword("ZONAL.FRONT.Set Low Beam =")
    def zonal_front_set_low_beam(self, state: str) -> None:
        self._domain.set_low_beam(state)

    @keyword("VERIFY.Low Beam State ==")
    def verify_low_beam_state(self, state: str) -> None:
        self._domain.verify_low_beam(state)

    @keyword("VERIFY.Door State ==")
    def verify_door_state(self, door: str, state: str) -> None:
        self._domain.verify_door_state(door, state)

    @keyword("ZONAL.CABIN.Set Seatbelt =")
    def zonal_cabin_set_seatbelt(self, seat: str, state: str) -> None:
        self._domain.set_seatbelt(seat, state)

    @keyword("ZONAL.CABIN.Command Window =")
    def zonal_cabin_command_window(self, door: str, command: str) -> None:
        self._domain.command_window(door, command)

    @keyword("HVAC.Set Temperature =")
    def hvac_set_temperature(self, temperature: float) -> None:
        self._domain.set_hvac_temperature(float(temperature))

    @keyword("VERIFY.HVAC Mode ==")
    def verify_hvac_mode(self, mode: str) -> None:
        self._domain.verify_hvac_mode(mode)

    @keyword("HVAC.Enable Demist")
    def hvac_enable_demist(self) -> None:
        self._domain.enable_demist()

    @keyword("VERIFY.Defrost ==")
    def verify_defrost(self, state: str) -> None:
        self._domain.verify_defrost(state)

    # ------------------------------------------------------------------
    # ADAS
    # ------------------------------------------------------------------
    @keyword("ADAS.Enable")
    def adas_enable(self, feature: str) -> None:
        self._domain.adas_enable(feature)

    @keyword("ADAS.Disable")
    def adas_disable(self, feature: str) -> None:
        self._domain.adas_disable(feature)

    @keyword("ADAS.Set Vehicle Speed =")
    def adas_set_vehicle_speed(self, speed: float) -> None:
        self._domain.adas_set_speed(float(speed))

    @keyword("ADAS.Inject Obstacle distance=")
    def adas_inject_obstacle(self, distance: float) -> None:
        self._domain.adas_inject_obstacle(float(distance))

    @keyword("VERIFY.WPP.ControlRequest ==")
    def verify_wpp_control_request(self, request: str) -> None:
        self._domain.verify_wpp_control_request(request)

    # ------------------------------------------------------------------
    # Energy / charging
    # ------------------------------------------------------------------
    @keyword("ENERGY.Connect EVSE")
    def energy_connect_evse(self) -> None:
        self._domain.connect_evse()

    @keyword("ENERGY.Disconnect EVSE")
    def energy_disconnect_evse(self) -> None:
        self._domain.disconnect_evse()

    @keyword("VERIFY.Charging Active ==")
    def verify_charging_active(self, expected: str) -> None:
        self._domain.verify_charging_active(expected.strip().upper() in {"TRUE", "1", "YES"})

    # ------------------------------------------------------------------
    # Brake / securement
    # ------------------------------------------------------------------
    @keyword("VEHICLE.Press Brake")
    def vehicle_press_brake(self) -> None:
        self._domain.press_brake()

    @keyword("VEHICLE.Release Brake")
    def vehicle_release_brake(self) -> None:
        self._domain.release_brake()

    @keyword("VERIFY.Cluster Brake Telltale ==")
    def verify_cluster_brake_telltale(self, state: str) -> None:
        self._domain.verify_brake_telltale(state)

    @keyword("VERIFY.Vehicle Securement State ==")
    def verify_vehicle_securement_state(self, state: str) -> None:
        self._domain.verify_securement_state(state)

    # ------------------------------------------------------------------
    # Lighting / environment
    # ------------------------------------------------------------------
    @keyword("LIGHTS.Set High Beam =")
    def lights_set_high_beam(self, state: str) -> None:
        self._domain.set_high_beam(state)

    @keyword("LIGHTS.Flash To Pass")
    def lights_flash_to_pass(self) -> None:
        self._domain.flash_to_pass()

    @keyword("VERIFY.Light Availability ==")
    def verify_light_availability(self, name: str, state: str) -> None:
        self._domain.verify_light_availability(name, state)

    # ------------------------------------------------------------------
    # Wipers
    # ------------------------------------------------------------------
    @keyword("WIPERS.Set Mode =")
    def wipers_set_mode(self, mode: str) -> None:
        self._domain.set_wiper_mode(mode)

    @keyword("WIPERS.Spray")
    def wipers_spray(self) -> None:
        self._domain.spray_washer()

    @keyword("VERIFY.Wipers State ==")
    def verify_wipers_state(self, state: str) -> None:
        self._domain.verify_wipers_state(state)

    # ------------------------------------------------------------------
    # Access
    # ------------------------------------------------------------------
    @keyword("ACCESS.Lock Vehicle")
    def access_lock_vehicle(self) -> None:
        self._domain.lock_vehicle()

    @keyword("ACCESS.Unlock Vehicle")
    def access_unlock_vehicle(self) -> None:
        self._domain.unlock_vehicle()

    @keyword("VERIFY.Door ==")
    def verify_door(self, door: str, state: str) -> None:
        self._domain.verify_door_state(door, state)

    @keyword("ACCESS.Open Luggage")
    def access_open_luggage(self) -> None:
        self._domain.open_luggage()

    @keyword("VERIFY.Luggage State ==")
    def verify_luggage_state(self, state: str) -> None:
        self._domain.verify_luggage_state(state)

    # ------------------------------------------------------------------
    # Pace / speed management
    # ------------------------------------------------------------------
    @keyword("PACE.Enable Limiter")
    def pace_enable_limiter(self) -> None:
        self._domain.enable_speed_limiter()

    @keyword("PACE.Set Limit =")
    def pace_set_limit(self, value: float) -> None:
        self._domain.set_speed_limit(float(value))

    @keyword("VERIFY.Speed Limit Status ==")
    def verify_speed_limit_status(self, status: str) -> None:
        self._domain.verify_speed_limit_status(status)

    # ------------------------------------------------------------------
    # ECU health
    # ------------------------------------------------------------------
    @keyword("ECU.Ping")
    def ecu_ping(self, ecu: str) -> None:
        self._domain.ecu_ping(ecu)

    def get_keyword_names(self) -> List[str]:  # pragma: no cover - Robot hook
        return [
            "PRECOND.Ensure Standby",
            "PRECOND.Ensure In Use",
            "PRECOND.Ensure Driving",
            "PRECOND.Ensure Charging",
            "PRECOND.Ensure HVAC Base",
            "PRECOND.Ensure Lighting Base",
            "BUS.Get Signal",
            "BACKEND.Send Command",
            "BACKEND.Wait For Ack",
            "BACKEND.Assert Vehicle Consistency",
            "CAPTURE.Start",
            "CAPTURE.Stop",
            "EVIDENCE.Snapshot",
            "DIAG.Read DTC",
            "DIAG.Clear DTC",
            "DIAG.Verify No Active DTC",
            "VERIFY.No Active DTCs ECU",
            "VERIFY.No Communication Faults",
            "RTCU.Trigger ECall",
            "RTCU.Cancel ECall",
            "BACKEND.Send Remote Lock",
            "BACKEND.Wait Ack",
            "VERIFY.Emergency LED ==",
            "VERIFY.PSAP Session Established ==",
            "SOMEIP.Wait Field",
            "VERIFY.Cluster Telltale ==",
            "BRAIN.Set Securement State =",
            "VERIFY.Securement State ==",
            "WIRED.Set",
            "VERIFY.WIRED Output ==",
            "BUS.Verify Signal ==",
            "ZONAL.FRONT.Set Door =",
            "ZONAL.FRONT.Set Low Beam =",
            "VERIFY.Low Beam State ==",
            "VERIFY.Door State ==",
            "ZONAL.CABIN.Set Seatbelt =",
            "ZONAL.CABIN.Command Window =",
            "HVAC.Set Temperature =",
            "VERIFY.HVAC Mode ==",
            "HVAC.Enable Demist",
            "VERIFY.Defrost ==",
            "ADAS.Enable",
            "ADAS.Disable",
            "ADAS.Set Vehicle Speed =",
            "ADAS.Inject Obstacle distance=",
            "VERIFY.WPP.ControlRequest ==",
            "ENERGY.Connect EVSE",
            "ENERGY.Disconnect EVSE",
            "VERIFY.Charging Active ==",
            "VEHICLE.Press Brake",
            "VEHICLE.Release Brake",
            "VERIFY.Cluster Brake Telltale ==",
            "VERIFY.Vehicle Securement State ==",
            "LIGHTS.Set High Beam =",
            "LIGHTS.Flash To Pass",
            "VERIFY.Light Availability ==",
            "WIPERS.Set Mode =",
            "WIPERS.Spray",
            "VERIFY.Wipers State ==",
            "ACCESS.Lock Vehicle",
            "ACCESS.Unlock Vehicle",
            "VERIFY.Door ==",
            "ACCESS.Open Luggage",
            "VERIFY.Luggage State ==",
            "PACE.Enable Limiter",
            "PACE.Set Limit =",
            "VERIFY.Speed Limit Status ==",
            "ECU.Ping",
        ]

    def _normalize_signals(self, signals: Sequence[str]) -> Iterable[str]:
        if len(signals) == 1:
            token = signals[0]
            if "," in token:
                return [part.strip() for part in token.split(",") if part.strip()]
        return [signal.strip() for signal in signals if signal.strip()]


__all__ = ["DomainKeywords"]
