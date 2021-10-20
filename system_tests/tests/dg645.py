import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim
import time

DEVICE_PREFIX = "DG645_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("DG645"),
        "macros": {},
        "emulator": "Dg645",
    },
]

TEST_MODES = [TestModes.DEVSIM]


class Dg645Tests(unittest.TestCase):
    """
    Tests for the Dg645 IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Dg645", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_trigger_source_set_THEN_readback_correct(self):
        test_data = ("Internal", "Ext rising edge",
                     "Ext falling edge", "SS ext rise edge",
                     "SS ext fall edge", "Single shot", "Line")
        for i in range(len(test_data)):
            self.ca.assert_setting_setpoint_sets_readback(i, "TriggerSourceMI", "TriggerSource:SP", test_data[i])

    def test_WHEN_trigger_threshold_set_THEN_readback_correct(self):
        self.ca.set_pv_value("TriggerLevelAO", 0.5)
        time.sleep(1)
        self.ca.process_pv("TriggerLevelAO")
        time.sleep(1)
        self.ca.process_pv("TriggerLevelAI")
        time.sleep(1)
        self.ca.assert_that_pv_is("TriggerLevelAI", 0.5)
        # test_data = (0.5, 1.25, 4.52, 1.12, 0.53)
        # for data in test_data:
        # self.ca.assert_setting_setpoint_sets_readback(data, readback_pv="TriggerLevelAI", set_point_pv="TriggerLevelAO")

    def test_WHEN_logic_button_pressed_THEN_correct_logic_set(self):
        channels = ("T0", "AB", "CD", "EF")
        for channel in channels:
            # test TTL
            self.ca.process_pv(channel + "LogicTTL:SP")
            self.ca.assert_that_pv_is(channel + "LogicTTL:RB", 1)
            self.ca.assert_that_pv_is(channel + "LogicNIM:RB", 0)
            self.ca.assert_that_pv_is(channel + "LogicNR:RB", 0)
            self.ca.assert_that_pv_is(channel + "OutputAmpAI", 4)
            self.ca.assert_that_pv_is(channel + "OutputOffsetAI", 0)

            # test NIM
            self.ca.process_pv(channel + "LogicNIM:SP")
            self.ca.assert_that_pv_is(channel + "LogicTTL:RB", 0)
            self.ca.assert_that_pv_is(channel + "LogicNIM:RB", 1)
            self.ca.assert_that_pv_is(channel + "LogicNR:RB", 0)
            self.ca.assert_that_pv_is(channel + "OutputAmpAI", 0.8)
            self.ca.assert_that_pv_is(channel + "OutputOffsetAI", -0.8)

            # test NR
            self.ca.set_pv_value(channel + "OutputAmpAO", 0)
            self.ca.set_pv_value(channel + "OutputOffsetAO", 0)
            self.ca.assert_that_pv_is(channel + "LogicTTL:RB", 0)
            self.ca.assert_that_pv_is(channel + "LogicNIM:RB", 0)
            self.ca.assert_that_pv_is(channel + "LogicNR:RB", 1)
            self.ca.assert_that_pv_is(channel + "OutputAmpAI", 0)
            self.ca.assert_that_pv_is(channel + "OutputOffsetAI", -0)

    def test_WHEN_polarity_button_pressed_THEN_correct_polarity_set(self):
        channels = ("T0", "AB", "CD", "EF")
        for channel in channels:
            # test positive
            self.ca.set_pv_value(channel + "OutputPolarity:SP", 1)
            self.ca.assert_that_pv_is(channel + "OutputPolarityBI.RVAL", 1)
            self.ca.assert_that_pv_is(channel + "OutputPolarity_OFF", 0)

            # test negative
            self.ca.set_pv_value(channel + "OutputPolarity:SP", 0)
            self.ca.assert_that_pv_is(channel + "OutputPolarityBI.RVAL", 0)
            self.ca.assert_that_pv_is(channel + "OutputPolarity_OFF", 1)

    def calculate_delay(self, count, unit):
        units_map = {"s": 1, "ms": 0.001, "us": 0.000001, "ns": 0.000000001, "ps": 0.000000000001}
        if unit not in units_map:
            raise AssertionError("Unexpected unit: " + str(unit))
        return round(count * units_map[unit], 12)

    def set_channel_delay(self, chan, ref, dlay, unit):
        self.ca.set_pv_value(str(chan) + "Reference:SP", ref)
        self.ca.set_pv_value(str(chan) + "Delay:SP", str(dlay))
        self.ca.set_pv_value(str(chan) + "DelayUnit:SP", unit)
        self.ca.set_pv_value(str(chan) + "DelayButton", 1)
        return self.calculate_delay(dlay, unit)

    def check_channel_delay(self, chan, ref, dlay, unit):
        self.ca.assert_that_pv_is(chan + "ReferenceMI", ref)
        # We might want to change read back display logic in the future so best to calculate
        # if outcome is correct rather than expect same exact values as on input
        count_received = self.ca.get_pv_value(chan + "Delay:RB")
        unit_received = self.ca.get_pv_value(chan + "DelayUnit:RB.SVAL")
        value_left = self.calculate_delay(count_received, unit_received)
        value_right = self.calculate_delay(dlay, unit)
        if not (value_left == value_right):
            raise AssertionError("Incorrect read back: " + str(value_left) + " != " + str(value_right))

    def set_all_channels(self, dataset):
        # data format: ((target, delay, unit), )
        channels = ("A", "B", "C", "D", "E", "F")
        assert (len(dataset) == len(channels))
        current_max = 0
        for i in range(len(channels)):
            current_max = max(current_max, self.set_channel_delay(channels[i], dataset[i][0], dataset[i][1],
                                                                  dataset[i][2]))
            self.check_channel_delay(channels[i], dataset[i][0], dataset[i][1], dataset[i][2])
        return current_max

    def test_WHEN_delay_set_THEN_readback_correct(self):
        channels = ("A", "B", "C", "D", "E", "F")
        testing_values = (("T0", 1, "us"), ("T0", 31, "us"), ("F", 22, "ms"), ("E", 12.3, "us"),
                          ("T0", 1.1111, "s"), ("T0", 4324155, "ps"))
        current_max = 0
        for i in range(len(testing_values)):
            set_val = self.set_channel_delay(channels[i], testing_values[i][0], testing_values[i][1],
                                             testing_values[i][2])
            self.check_channel_delay(channels[i], testing_values[i][0], testing_values[i][1], testing_values[i][2])

            # T1 is max function of other channels so we check it for every channel change
            current_max = max(current_max, set_val)
            t1_actual = self.calculate_delay(self.ca.get_pv_value("T1Delay:RB"),
                                             self.ca.get_pv_value("T1DelayUnit:RB.SVAL"))
            if not (t1_actual == current_max):
                raise AssertionError("T1 incorrect value, expecting: " + str(current_max) +
                                     ", received: " + str(t1_actual))

    # Check that T1 width is correct. T1 width = T1-T0. T0 and T1 behave differently
    # to other channels so they require 'special treatment'.
    def test_WHEN_delays_set_THEN_trigger_widths_readback_correct(self):
        delays_dataset = (("T0", 1, "us"), ("T0", 31, "us"), ("F", 22, "ms"), ("E", 12.3, "us"),
                          ("T0", 1.1111, "s"), ("T0", 4324155, "ps"))
        current_max = self.set_all_channels(delays_dataset)

        t0_delay_rb = self.calculate_delay(self.ca.get_pv_value("T0Delay:RB"),
                                           self.ca.get_pv_value("T0DelayUnit:RB.SVAL"))
        t1_delay_rb = self.calculate_delay(self.ca.get_pv_value("T1Delay:RB"),
                                           self.ca.get_pv_value("T1DelayUnit:RB.SVAL"))
        t1_width_expected = t0_delay_rb + current_max
        if not (t1_width_expected == t0_delay_rb + t1_delay_rb):
            raise AssertionError("T1 width incorrect, expected: " + str(t1_width_expected) + ", received: " +
                                 str(t0_delay_rb + t1_delay_rb))

    # performs a depth-limited recursive search to get final width of a channel
    def get_channel_width(self, channel_data, which, width=0, depth=0):
        # channel_data: (("REF_CHAN", COUNT, "UNIT"), )
        delays_dict = {"T0": 0, "T1": 1, "A": 2, "B": 3, "C": 4, "D": 5, "E": 6, "F": 7}
        current = channel_data[delays_dict[which]]
        my_width = round(width + self.calculate_delay(current[1], current[2]), 12)

        if depth > 8:
            raise AssertionError("Endless reference loop detected in channel data. Test data invalid.")

        # referencing T0 stops the search
        if current[0] == "T0":
            return my_width
        else:
            return self.get_channel_width(channel_data, current[0], my_width, depth + 1)

    def test_WHEN_delays_set_THEN_channel_widths_correct(self):
        channel_data = (("", 0, "s"), ("", 0, "s"), ("T0", 1, "us"), ("T0", 31, "us"), ("F", 22, "ms"),
                        ("E", 12.3, "us"), ("T0", 1.1111, "s"), ("T0", 4324155, "ps"))
        self.set_all_channels(channel_data[2:])
        channels = ('A', 'B', 'C', 'D', 'E', 'F')
        widths = []
        for channel in channels:
            expected = self.get_channel_width(channel_data, channel)
            received = self.calculate_delay(self.ca.get_pv_value(str(channel) + "DelayWidth:RB"),
                                            self.ca.get_pv_value(str(channel) + "DelayWidthUnit:RB.SVAL"))
            if not expected == received:
                raise AssertionError("Delay width incorrect, expected: " + str(expected) +
                                     ", received: " + str(received))
            # Collect channel widths for the next step
            widths.append(expected)

        # Total width is a sum of both widths
        channels_total = ("AB", "CD", "EF")
        for i in range(len(channels_total)):
            expected = round(widths[2 * i] + widths[2 * i + 1], 12)
            received = self.calculate_delay(self.ca.get_pv_value(str(channels_total[i]) + "DelayWidth:RB"),
                                            self.ca.get_pv_value(str(channels_total[i]) + "DelayWidthUnit:RB.SVAL"))
            if not expected == received:
                raise AssertionError("Total delay width incorrect, expected: " + str(expected) +
                                     ", received: " + str(received))

    def test_WHEN_invalid_action_performed_THEN_error_queue_entry_added(self):
        # First set to something valid
        self.set_channel_delay('A', 'T0', 1, 'us')
        self.check_channel_delay('A', 'T0', 1, 'us')
        # Perform illegal actions to overwrite the queue (reference illegal channel - self reference)
        # We expect channel reference change not to be applied
        for i in range(10):
            self.set_channel_delay('A', 'A', 1, 'us')
            # Check that no changes were made to the referenced channel
            self.check_channel_delay('A', 'T0', 1, 'us')
        # Set to something correct again
        self.set_channel_delay('A', 'T0', 1, 'us')
        self.check_channel_delay('A', 'T0', 1, 'us')

        # Check expected state of error queue
        # We expect to have 'status ok' as latest error message, followed by 9 'illegal link' messages
        latest_error = self.ca.get_pv_value("ERQ9")
        assert "status ok" in latest_error.lower()
        for i in range(9):
            error = self.ca.get_pv_value("ERQ" + str(i))
            assert "illegal link" in error.lower()

        # Add another error and check that the data shifted accordingly
        self.set_channel_delay('A', 'A', 1, 'us')
        self.check_channel_delay('A', 'T0', 1, 'us')
        assert "illegal link" in self.ca.get_pv_value("ERQ9").lower()
        assert "status ok" in self.ca.get_pv_value("ERQ8").lower()
        for i in range(8):
            error = self.ca.get_pv_value("ERQ" + str(i))
            assert "illegal link" in error.lower()
