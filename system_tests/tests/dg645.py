# pyright: reportMissingImports=false
import unittest

from parameterized import parameterized
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import ProcServLauncher, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, parameterized_list

DEVICE_PREFIX = "DG645_01"
EMULATOR_NAME = "Dg645"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("DG645"),
        "macros": {},
        "emulator": EMULATOR_NAME,
        "ioc_launcher_class": ProcServLauncher,
    },
]

TEST_MODES = [TestModes.DEVSIM]

OUTPUT_CHANNELS = ["T0", "AB", "CD", "EF", "GH"]
DEVICE_CHANNELS = ("T0", "T1", "A", "B", "C", "D", "E", "F", "G", "H")


class Dg645Tests(unittest.TestCase):
    """
    Tests for the Dg645 IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    @parameterized.expand(
        [
            ("Internal", 0),
            ("Ext rising edge", 1),
            ("Ext falling edge", 2),
            ("SS ext rise edge", 3),
            ("SS ext fall edge", 4),
            ("Single shot", 5),
            ("Line", 6),
        ]
    )
    def test_WHEN_trigger_source_set_THEN_readback_correct(self, expected_value, value):
        self.ca.assert_setting_setpoint_sets_readback(
            value, "TriggerSourceMI", "TRIGGERSOURCE:SP", expected_value
        )

    @parameterized.expand([(0.5,), (1.25,), (4.52,), (1.12,), (0.53,)])
    def test_WHEN_trigger_threshold_set_THEN_readback_correct(self, test_data):
        self.ca.assert_setting_setpoint_sets_readback(
            test_data, "TriggerLevelAI", "TriggerLevelAO", timeout=30
        )

    # OutputAmpAI and OutputOffsetAI values control which logic flag is currently applied, as demonstrated by VI
    # 4, 0 = TTL
    # 0.8, -0.8 = NIM
    # Any other combination = NR
    @parameterized.expand(parameterized_list(OUTPUT_CHANNELS))
    def test_WHEN_logic_button_pressed_THEN_correct_logic_set_TTL(self, _, channel):
        self.ca.process_pv(channel + "LOGICTTL:SP")
        self.ca.assert_that_pv_is(channel + "LOGICTTL:RB", 1)
        self.ca.assert_that_pv_is(channel + "LOGICNIM:RB", 0)
        self.ca.assert_that_pv_is(channel + "LOGICNR:RB", 0)
        self.ca.assert_that_pv_is(channel + "OutputAmpAI", 4)
        self.ca.assert_that_pv_is(channel + "OutputOffsetAI", 0)

    @parameterized.expand(parameterized_list(OUTPUT_CHANNELS))
    def test_WHEN_logic_button_pressed_THEN_correct_logic_set_NIM(self, _, channel):
        self.ca.process_pv(channel + "LOGICNIM:SP")
        self.ca.assert_that_pv_is(channel + "LOGICTTL:RB", 0)
        self.ca.assert_that_pv_is(channel + "LOGICNIM:RB", 1)
        self.ca.assert_that_pv_is(channel + "LOGICNR:RB", 0)
        self.ca.assert_that_pv_is(channel + "OutputAmpAI", 0.8)
        self.ca.assert_that_pv_is(channel + "OutputOffsetAI", -0.8)

    @parameterized.expand(parameterized_list(OUTPUT_CHANNELS))
    def test_WHEN_logic_button_pressed_THEN_correct_logic_set_NR(self, _, channel):
        self.ca.set_pv_value(channel + "OutputAmpAO", 0)
        self.ca.set_pv_value(channel + "OutputOffsetAO", 0)
        self.ca.assert_that_pv_is(channel + "LOGICTTL:RB", 0)
        self.ca.assert_that_pv_is(channel + "LOGICNIM:RB", 0)
        self.ca.assert_that_pv_is(channel + "LOGICNR:RB", 1)
        self.ca.assert_that_pv_is(channel + "OutputAmpAI", 0)
        self.ca.assert_that_pv_is(channel + "OutputOffsetAI", -0)

    @parameterized.expand(parameterized_list(OUTPUT_CHANNELS))
    def test_WHEN_polarity_button_pressed_THEN_correct_polarity_set_positive(self, _, channel):
        self.ca.set_pv_value(channel + "OUTPUTPOLARITY:SP", 1)
        self.ca.assert_that_pv_is(channel + "OutputPolarityBI.RVAL", 1)
        self.ca.assert_that_pv_is(channel + "OUTPUTPOLARITY_OFF", 0)

    @parameterized.expand(parameterized_list(OUTPUT_CHANNELS))
    def test_WHEN_polarity_button_pressed_THEN_correct_polarity_set_negative(self, _, channel):
        self.ca.set_pv_value(channel + "OUTPUTPOLARITY:SP", 0)
        self.ca.assert_that_pv_is(channel + "OutputPolarityBI.RVAL", 0)
        self.ca.assert_that_pv_is(channel + "OUTPUTPOLARITY_OFF", 1)

    def calculate_delay(self, count, unit):
        units_map = {"s": 1, "ms": 0.001, "us": 0.000001, "ns": 0.000000001, "ps": 0.000000000001}
        self.assertIn(unit, units_map, "Unexpected unit: " + str(unit))
        return round(count * units_map[unit], 12)

    def set_channel_delay(self, chan, ref, dlay, unit, check_readback=False):
        self.ca.set_pv_value(str(chan) + "REFERENCE:SP", ref)
        self.ca.set_pv_value(str(chan) + "DELAY:SP", str(dlay))
        self.ca.set_pv_value(str(chan) + "DELAYUNIT:SP", unit)
        self.ca.set_pv_value(str(chan) + "DELAYBUTTON", 1)
        # Flag to also check if channel was saved without errors
        if check_readback:
            self.check_channel_delay(chan, ref, dlay, unit)
        return self.calculate_delay(dlay, unit)

    def check_channel_delay(self, chan, ref, dlay, unit):
        self.ca.assert_that_pv_is(chan + "ReferenceMI", ref)
        count_received = self.ca.get_pv_value(chan + "DELAY:RB")
        unit_received = self.ca.get_pv_value(chan + "DELAYUNIT:RB")
        value_left = self.calculate_delay(count_received, unit_received)
        value_right = self.calculate_delay(dlay, unit)
        self.assertEqual(
            value_left,
            value_right,
            "Incorrect read back: " + str(value_left) + " != " + str(value_right),
        )

    # Returns max delay of all channels set
    def set_all_channels(self, dataset):
        channels_to_set = DEVICE_CHANNELS[2:]
        self.assertEqual(len(dataset), len(channels_to_set), "Incorrect dataset provided")
        current_max = 0
        for i in range(len(dataset)):
            current_max = max(
                current_max,
                self.set_channel_delay(
                    channels_to_set[i], dataset[i][0], dataset[i][1], dataset[i][2]
                ),
            )
            self.check_channel_delay(
                channels_to_set[i], dataset[i][0], dataset[i][1], dataset[i][2]
            )
        return current_max

    @parameterized.expand(
        [
            ("A", "T0", 1, "us"),
            ("B", "T0", 31, "us"),
            ("C", "F", 22, "ms"),
            ("D", "E", 12.3, "us"),
            ("E", "T0", 1.1111, "s"),
            ("F", "T0", 4324155, "ps"),
            ("G", "T0", 66, "ms"),
            ("H", "T0", 99, "ms"),
        ]
    )
    def test_WHEN_delay_set_THEN_readback_correct(self, channel, reference, delay, unit):
        self.set_channel_delay(channel, reference, delay, unit, True)

    # T1_delay = T0_delay + current_max_delay
    # We must set all channels to measure this
    @parameterized.expand(
        [
            (
                (
                    ("T0", 1, "us"),
                    ("T0", 31, "us"),
                    ("F", 22, "ms"),
                    ("E", 12.3, "us"),
                    ("T0", 1.1111, "s"),
                    ("T0", 4324155, "ps"),
                    ("T0", 4, "us"),
                    ("T0", 12, "us"),
                ),
            ),
            (
                (
                    ("T0", 5, "ns"),
                    ("F", 12, "ms"),
                    ("A", 153, "us"),
                    ("A", 3.3, "ms"),
                    ("T0", 4.1452, "ms"),
                    ("A", 344315, "ps"),
                    ("T0", 2, "us"),
                    ("T0", 4, "us"),
                ),
            ),
        ]
    )
    def test_WHEN_delays_set_THEN_T1_width_readback_correct(self, channel_settings):
        current_max = self.set_all_channels(channel_settings)
        t0_delay_rb = self.calculate_delay(
            self.ca.get_pv_value("T0DELAY:RB"), self.ca.get_pv_value("T0DELAYUNIT:RB")
        )
        t1_delay_rb = self.calculate_delay(
            self.ca.get_pv_value("T1DELAY:RB"), self.ca.get_pv_value("T1DELAYUNIT:RB")
        )
        t1_width_expected = t0_delay_rb + current_max
        self.assertEqual(
            t1_width_expected,
            t0_delay_rb + t1_delay_rb,
            "T1 width incorrect, expected: "
            + str(t1_width_expected)
            + ", received: "
            + str(t0_delay_rb + t1_delay_rb),
        )

    # performs a depth-limited recursive search to get final width of a channel
    def get_channel_width(self, channel_data, which, width=0, depth=0):
        delays_dict = {
            "T0": 0,
            "T1": 1,
            "A": 2,
            "B": 3,
            "C": 4,
            "D": 5,
            "E": 6,
            "F": 7,
            "G": 8,
            "H": 9,
        }
        current = channel_data[delays_dict[which]]
        my_width = round(width + self.calculate_delay(current[1], current[2]), 12)

        # on valid settings, the depth should never reach 8
        self.assertLess(
            depth, 8, "Endless reference loop detected in channel data. Test data invalid."
        )

        # referencing T0 stops the search
        if current[0] == "T0":
            return my_width
        else:
            return self.get_channel_width(channel_data, current[0], my_width, depth + 1)

    # returns calculated channel width if it matches the settings
    def check_channel_width_matches_settings(self, channel_settings, channel):
        expected = self.get_channel_width(channel_settings, channel)
        received = self.calculate_delay(
            self.ca.get_pv_value(str(channel) + "DELAYWIDTH:RB"),
            self.ca.get_pv_value(str(channel) + "DELAYWIDTHUNIT:RB.SVAL"),
        )
        self.assertEqual(
            expected,
            received,
            "Delay width incorrect, expected: " + str(expected) + ", received: " + str(received),
        )

    # Each channel has a width which is equal to this channel's delay plus delay of referenced channel
    # Since a chain of references between channels can include all channels, we must set settings of
    # all channels before checking this
    @parameterized.expand(
        [
            (
                (
                    ("", 0, "s"),
                    ("", 0, "s"),
                    ("T0", 1, "us"),
                    ("T0", 31, "us"),
                    ("F", 22, "ms"),
                    ("E", 12.3, "us"),
                    ("T0", 1.1111, "s"),
                    ("T0", 4324155, "ps"),
                    ("T0", 4, "us"),
                    ("T0", 7, "us"),
                ),
            ),
            (
                (
                    ("", 0, "s"),
                    ("", 0, "s"),
                    ("T0", 5, "ns"),
                    ("F", 12, "ms"),
                    ("A", 153, "us"),
                    ("A", 3.3, "ms"),
                    ("T0", 4.1452, "ms"),
                    ("A", 344315, "ps"),
                    ("T0", 55.12, "us"),
                    ("T0", 72.8, "us"),
                ),
            ),
        ]
    )
    def test_WHEN_delays_set_THEN_channel_widths_correct(self, channel_settings):
        # We are not checking this for T0 and T1 which are the first 2 channels
        tested_channels = DEVICE_CHANNELS[2:]
        self.set_all_channels(channel_settings[2:])
        for channel in tested_channels:
            self.check_channel_width_matches_settings(channel_settings, channel)

    def check_total_channel_width(self, channel_a, channel_b):
        expected = abs(round(channel_a[1] - channel_b[1], 12))
        received = self.calculate_delay(
            self.ca.get_pv_value(channel_a[0] + channel_b[0] + "DELAYWIDTH:RB"),
            self.ca.get_pv_value(channel_a[0] + channel_b[0] + "DELAYWIDTHUNIT" ":RB.SVAL"),
        )
        self.assertEqual(
            expected,
            received,
            "Total delay width incorrect, expected: "
            + str(expected)
            + ", received: "
            + str(received),
        )

    # Total width is a sum of width of 2 channels. For example: AB_width = A_width + B_width
    @parameterized.expand([("A", "B"), ("C", "D"), ("E", "F"), ("G", "H")])
    def test_WHEN_delays_set_THEN_total_channel_widths_correct(self, name_a, name_b):
        width_a = self.calculate_delay(
            self.ca.get_pv_value(name_a + "DELAYWIDTH:RB"),
            self.ca.get_pv_value(name_a + "DELAYWIDTHUNIT:RB.SVAL"),
        )
        width_b = self.calculate_delay(
            self.ca.get_pv_value(name_b + "DELAYWIDTH:RB"),
            self.ca.get_pv_value(name_b + "DELAYWIDTHUNIT:RB.SVAL"),
        )
        self.check_total_channel_width((name_a, width_a), (name_b, width_b))

    def check_error_queue(self, start, length, message):
        assert 0 <= start <= 9
        assert 0 <= start + length <= 10
        i = start
        while i < start + length:
            error = self.ca.get_pv_value("ERQ" + str(i))
            self.assertIn(message, error.lower())
            i += 1

    # This will fill the error queue with 'illegal link' messages
    def overwrite_error_queue(self):
        # First set to something valid
        self.set_channel_delay("A", "T0", 1, "us", True)
        for i in range(10):
            # Reference illegal channel - self reference
            self.set_channel_delay("A", "A", 1, "us")
            # Check that no changes were made to the referenced channel
            self.check_channel_delay("A", "T0", 1, "us")

    def test_WHEN_invalid_action_performed_THEN_error_queue_entry_added(self):
        self.overwrite_error_queue()
        self.check_error_queue(0, 9, "illegal link")

        # We expect to have 'status ok' as latest error message, followed by 9 'illegal link' messages
        self.set_channel_delay("A", "T0", 1, "us", True)
        self.check_error_queue(0, 8, "illegal link")
        self.check_error_queue(9, 1, "status ok")

        # Add another error and check that the data shifted accordingly
        self.set_channel_delay("A", "A", 1, "us")
        self.check_channel_delay("A", "T0", 1, "us")
        self.check_error_queue(0, 7, "illegal link")
        self.check_error_queue(8, 1, "status ok")
        self.check_error_queue(9, 1, "illegal link")
