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
        self.ca.set_pv_value("OFFSET", 10)
        self.ca.set_pv_value("DELAY", 20)
        self.ca.assert_that_pv_is("SUMMED_VALUE", 30)

    def test_Summed_Delay(self):
        self.ca.set_pv_value("ADLAYSCAL", 10)
        self.ca.set_pv_value("CDLAYSCAL", 20)
        self.ca.set_pv_value("ADELAYBUTTON", 1)
        self.ca.set_pv_value("CDELAYBUTTON", 1)
        self.ca.assert_that_pv_is("SUMMED_DELAY", 30)

    def test_Mode_Zero_Change_Mode_To_One(self):
        self.ca.set_pv_value("DELAY", 10)
        self.ca.set_pv_value("OFFSET", 5)
        self.ca.set_pv_value("MODE", "auto")
        self.ca.assert_that_pv_is("SET_MODE", 1)

    def test_Mode_Zero_Change_Mode_To_Two(self):
        self.ca.set_pv_value("DELAY", 5)
        self.ca.set_pv_value("OFFSET", 5)
        self.ca.set_pv_value("MODE", "auto")
        self.ca.assert_that_pv_is("SET_MODE", 2)

    @parameterized.expand([(0, 39900, 100, 1), (40000, 0, 0, 1), (10, -1, 0, 1), (10, -5, 5, 0)])
    def test_Mode_One_Error_Check(self, cdelay, delay, offset, err):
        self.ca.set_pv_value("CDELAY:SP", cdelay)
        self.ca.set_pv_value("CDELAYUNIT:SP", "us")
        self.ca.set_pv_value("CDELAYBUTTON", 1)
        self.ca.set_pv_value("OFFSET", offset)
        self.ca.set_pv_value("DELAY", delay)
        self.ca.set_pv_value("MODE", "1")
        self.ca.set_pv_value("ERROR.PROC", "1")
        self.ca.assert_that_pv_is("ERROR", err)

    @parameterized.expand(
        [
            (0, 40000, 0, 1),
            (40000, 0, 0, 0),
            (0, 0, 0, 1),
            (10, -1, 0, 0),
            (10, -5, -6, 1),
        ]
    )
    def test_Mode_Two_Error_Check(self, cdelay, delay, offset, err):
        self.ca.set_pv_value("CDELAY:SP", cdelay)
        self.ca.set_pv_value("CDELAYUNIT:SP", "us")
        self.ca.set_pv_value("CDELAYBUTTON", 1)
        self.ca.set_pv_value("OFFSET", offset)
        self.ca.set_pv_value("DELAY", delay)
        self.ca.set_pv_value("MODE", "2")
        self.ca.set_pv_value("ERROR.PROC", "1")
        self.ca.assert_that_pv_is("ERROR", err)
