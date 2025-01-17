# pyright: reportMissingImports=false
import unittest

from parameterized import parameterized
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import ProcServLauncher, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc

DEVICE_PREFIX = "DG645_01"
EMULATOR_NAME = "Dg645"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("DG645"),
        "macros": {
            "APPLICATION": "LITRON",
        },
        "emulator": EMULATOR_NAME,
        "ioc_launcher_class": ProcServLauncher,
    },
]

TEST_MODES = [TestModes.DEVSIM]


class Dg645LLTTests(unittest.TestCase):
    """
    Tests for the Dg645 Litron Laser Timing Control IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_Summed_Value(self):
        self.ca.set_pv_value("DELAY", 10)
        self.ca.set_pv_value("OFFSET", 20)
        self.ca.set_pv_value("SET.PROC", "1")
        self.ca.assert_that_pv_is("ADelayAO", 0.00003)

    def test_Summed_Delay(self):
        self.ca.set_pv_value("ADelayAO", 0.00001)
        self.ca.set_pv_value("CDelayAO", 0.00002)
        self.ca.assert_that_pv_is("SUMMED_DELAY", 30)

    @parameterized.expand([(0, 39900, 100, 1)])
    def test_When_In_Error_Can_Not_Set_Delay(self, cdelay, delay, offset, err):
        self.ca.set_pv_value("CDelayAO", cdelay)
        self.ca.set_pv_value("ADelayAO", 0)
        self.ca.set_pv_value("OFFSET", offset)
        self.ca.set_pv_value("DELAY", delay)
        self.ca.set_pv_value("MODE", "1")
        self.ca.set_pv_value("SET.PROC", "1")
        self.ca.assert_that_pv_is("ERROR", err)
        self.ca.assert_that_pv_is("ADelayAO", 0)

    def test_Mode_Auto_Change_Mode_To_One(self):
        self.ca.set_pv_value("DELAY", 10)
        self.ca.set_pv_value("OFFSET", 5)
        self.ca.set_pv_value("MODE", "auto")
        self.ca.assert_that_pv_is("SET_MODE", 1)

    def test_Mode_Auto_Change_Mode_To_Two(self):
        self.ca.set_pv_value("DELAY", 5)
        self.ca.set_pv_value("OFFSET", 5)
        self.ca.set_pv_value("MODE", "auto")
        self.ca.assert_that_pv_is("SET_MODE", 2)

    @parameterized.expand(
        [(0, 39900, 100, 1), (0.04, 0, 0, 1), (0.00001, -1, 0, 1), (0.00001, -5, 5, 0)]
    )
    def test_Mode_One_Error_Check(self, cdelay, delay, offset, err):
        self.ca.set_pv_value("CDelayAO", cdelay)
        self.ca.set_pv_value("OFFSET", offset)
        self.ca.set_pv_value("DELAY", delay)
        self.ca.set_pv_value("MODE", "1")
        self.ca.set_pv_value("SET.PROC", "1")
        self.ca.assert_that_pv_is("ERROR", err)

    @parameterized.expand(
        [
            (0, 40000, 0, 1),
            (0.04, 0, 0, 0),
            (0, 0, 0, 1),
            (0.00001, -1, 0, 0),
            (0.00001, -5, -6, 1),
        ]
    )
    def test_Mode_Two_Error_Check(self, cdelay, delay, offset, err):
        self.ca.set_pv_value("CDelayAO", cdelay)
        self.ca.set_pv_value("OFFSET", offset)
        self.ca.set_pv_value("DELAY", delay)
        self.ca.set_pv_value("MODE", "2")
        self.ca.set_pv_value("SET.PROC", "1")
        self.ca.assert_that_pv_is("ERROR", err)
