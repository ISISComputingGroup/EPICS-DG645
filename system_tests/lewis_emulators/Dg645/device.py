from collections import OrderedDict
from typing import Callable

from lewis.devices import StateMachineDevice

from .states import DefaultState, State


class SimulatedDg645(StateMachineDevice):
    def _initialize_data(self) -> None:
        self.identification = "SRS DG645,s/n001332,ver1.07.10E"
        self.delays = [
            (0, 0.0),  # T0
            (0, 0.0),  # T1
            (0, 0.0),  # A
            (0, 0.0),  # B
            (0, 0.0),  # C
            (0, 0.0),  # D
            (0, 0.0),  # E
            (0, 0.0),  # F
            (0, 0.0),  # G
            (0, 0.0),  # H
        ]
        self.trigger_source = 0
        self.level_amplitude = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.level_offset = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.level_polarity = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.trigger_level = 0
        self.error_queue = []

        # Error codes
        self.NO_ERROR_IN_QUEUE_CODE = 0
        self.ILLEGAL_VALUE_ERROR_CODE = 10
        self.ILLEGAL_LINK_ERROR_CODE = 13

    def _get_state_handlers(self) -> dict[str, State]:
        return {
            "default": DefaultState(),
        }

    def _get_initial_state(self) -> str:
        return "default"

    def _get_transition_handlers(self) -> dict[tuple[str, str], Callable[[], bool]]:
        return OrderedDict([])

    def update_trigger_delays(self) -> None:
        # T0 is the base - always 0
        # T1 is always the longest delay
        t1_delay = 0
        for delay in self.delays[2:]:
            if delay[1] > t1_delay:
                t1_delay = delay[1]
        self.delays[1] = (0, t1_delay)

    def get_error(self) -> int:
        if len(self.error_queue) > 0:
            return self.error_queue.pop(0)
        else:
            return self.NO_ERROR_IN_QUEUE_CODE

    def add_error(self, err: int) -> None:
        self.error_queue.append(err)
        # Device holds a queue of errors of size 20
        self.error_queue = self.error_queue[:20]

    # Rounds up numbers of precision of 10e-12 and lower to 5 or 0
    def round_value_pcs(self, value: float) -> float:
        new_value = "{:.12f}".format(float(value))
        new_value = float(new_value) * 1e12
        new_value = 5 * round(new_value / 5)
        new_value *= 1e-12
        return new_value
