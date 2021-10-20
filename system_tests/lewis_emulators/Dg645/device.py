from collections import OrderedDict
from .states import DefaultState
from lewis.devices import StateMachineDevice
import queue


class SimulatedDg645(StateMachineDevice):

    def _initialize_data(self):
        self.identification = "SRS DG645,s/n001332,ver1.07.10E"
        self.delays = [
            (0, 0),  # T0
            (0, 0),  # T1
            (0, 0),  # A
            (0, 0),  # B
            (0, 0),  # C
            (0, 0),  # D
            (0, 0),  # E
            (0, 0),  # F
            (0, 0),  # G
            (0, 0)  # H
        ]
        self.trigger_source = 0
        self.level_amplitude = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        ]
        self.level_offset = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        ]
        self.level_polarity = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        ]
        self.trigger_level = 0
        self.error_queue = []

    def _get_state_handlers(self):
        return {
            'default': DefaultState(),
        }

    def _get_initial_state(self):
        return 'default'

    def _get_transition_handlers(self):
        return OrderedDict([
        ])

    def update_trigger_delays(self):
        # T0 is the base - always 0
        # T1 is always the longest delay
        t1_delay = 0
        for delay in self.delays[2:]:
            if delay[1] > t1_delay:
                t1_delay = delay[1]
        self.delays[1] = (0, t1_delay)

    def get_error(self):
        if len(self.error_queue) > 0:
            return self.error_queue.pop()
        else:
            return 0

    def add_error(self, err):
        self.error_queue = [err] + self.error_queue[0:20]
