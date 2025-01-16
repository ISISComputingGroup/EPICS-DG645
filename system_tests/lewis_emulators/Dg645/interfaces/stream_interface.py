from lewis.adapters.stream import StreamInterface
from lewis.core.logging import has_log
from lewis.utils.command_builder import CmdBuilder

from lewis_emulators.Dg645.device import SimulatedDg645


@has_log
class Dg645StreamInterface(StreamInterface):
    def __init__(self) -> None:
        self._device: SimulatedDg645

    commands = {
        CmdBuilder("get_ident").escape("*IDN?").eos().build(),
        CmdBuilder("get_delay").escape("DLAY?").spaces().int().eos().build(),
        CmdBuilder("set_delay")
        .escape("DLAY")
        .spaces()
        .int()
        .optional(",")
        .spaces()
        .int()
        .optional(",")
        .spaces()
        .any()
        .eos()
        .build(),
        CmdBuilder("get_trigger_source").escape("TSRC?").eos().build(),
        CmdBuilder("set_trigger_source").escape("TSRC").spaces().int().eos().build(),
        CmdBuilder("get_level_amplitude").escape("LAMP?").spaces().int().eos().build(),
        CmdBuilder("set_level_amplitude")
        .escape("LAMP")
        .spaces()
        .spaces()
        .int()
        .optional(",")
        .spaces()
        .any()
        .eos()
        .build(),
        CmdBuilder("get_level_offset").escape("LOFF?").spaces().int().eos().build(),
        CmdBuilder("set_level_offset")
        .escape("LOFF")
        .spaces()
        .spaces()
        .int()
        .optional(",")
        .spaces()
        .any()
        .eos()
        .build(),
        CmdBuilder("get_level_polarity").escape("LPOL?").spaces().int().eos().build(),
        CmdBuilder("set_level_polarity")
        .escape("LPOL")
        .spaces()
        .int()
        .optional(",")
        .spaces()
        .any()
        .eos()
        .build(),
        CmdBuilder("get_last_error").escape("LERR?").eos().build(),
        CmdBuilder("set_clear_queue").escape("*CLS").eos().build(),
        CmdBuilder("get_trigger_level").escape("TLVL?").eos().build(),
        CmdBuilder("set_trigger_level").escape("TLVL").spaces().float().eos().build(),
        CmdBuilder("local_mode").escape("LCAL").eos().build(),
        CmdBuilder("remote_mode").escape("REMT").eos().build(),
        CmdBuilder("save_config").escape("*SAV").spaces().int().eos().build(),
        CmdBuilder("load_config").escape("*RCL").spaces().int().eos().build(),
        # Commands below are only defined but not implemented because without it, the Delaygen
        # ASYN driver would crash
        CmdBuilder("get_prescale_factor").escape("PRES?").spaces().int().eos().build(),
        CmdBuilder("get_prescale_phase_factor").escape("PHAS?").spaces().int().eos().build(),
        CmdBuilder("get_interface_config").escape("IFCF?").spaces().int().eos().build(),
        CmdBuilder("get_trigger_rate").escape("TRAT?").eos().build(),
        CmdBuilder("get_advanced_triggering_mode").escape("ADVT?").eos().build(),
        CmdBuilder("get_inhibit").escape("INHB?").eos().build(),
        CmdBuilder("get_ethernet_mac").escape("EMAC?").eos().build(),
        CmdBuilder("get_burst_count").escape("BURC?").eos().build(),
        CmdBuilder("get_burst_delay").escape("BURD?").eos().build(),
        CmdBuilder("get_burst_mode").escape("BURM?").eos().build(),
        CmdBuilder("get_burst_period").escape("BURP?").eos().build(),
        CmdBuilder("get_burst_t0").escape("BURT?").eos().build(),
        CmdBuilder("get_holdoff").escape("HOLD?").eos().build(),
        CmdBuilder("get_step_size_delay").escape("SSDL?").spaces().int().eos().build(),
    }

    in_terminator = "\n"
    out_terminator = "\r\n"

    # Trigger source can be selected from 6 enum values
    # which are represented by numbers 0-5
    def check_trigger_source_valid(self, new_trg_src: int) -> bool:
        if new_trg_src < 0 or new_trg_src > 6:
            return False
        return True

    def catch_all(self, command: str) -> None:
        pass

    def get_ident(self) -> str:
        return self._device.identification

    def get_delay(self, which: int) -> str:
        self._device.update_trigger_delays()
        return (
            str(self._device.delays[which][0])
            + ","
            + str("{:.12f}".format(float(self._device.delays[which][1])))
        )

    def set_delay(self, which: int, target: int, amount: float) -> None:
        if which == target or which == 0 or which == 1 or target == 1:
            self._device.add_error(self._device.ILLEGAL_LINK_ERROR_CODE)
            return
        # If the delay is set on the device to a precision of 10e-12 then
        # last digit is rounded to 5 or 0
        self._device.delays[which] = (target, self._device.round_value_pcs(amount))
        self._device.update_trigger_delays()

    def get_trigger_source(self) -> int:
        return self._device.trigger_source

    def set_trigger_source(self, new: int) -> None:
        if not self.check_trigger_source_valid(new):
            self._device.add_error(self._device.ILLEGAL_VALUE_ERROR_CODE)
        self._device.trigger_source = new

    def get_level_amplitude(self, which: int) -> int:
        return self._device.level_amplitude[which]

    def set_level_amplitude(self, which: int, new: int) -> None:
        self._device.level_amplitude[which] = new

    def get_level_offset(self, which: int) -> int:
        return self._device.level_offset[which]

    def set_level_offset(self, which: int, new: int) -> None:
        self._device.level_offset[which] = new

    def get_level_polarity(self, which: int) -> int:
        return self._device.level_polarity[which]

    def set_level_polarity(self, which: int, new: int) -> None:
        self._device.level_polarity[which] = new

    def get_last_error(self) -> int:
        return self._device.get_error()

    def set_clear_queue(self) -> None:
        self._device.error_queue = []

    def get_trigger_level(self) -> int:
        return self._device.trigger_level

    def set_trigger_level(self, new: int) -> None:
        self._device.trigger_level = new

    def local_mode(self) -> None:
        return

    def remote_mode(self) -> None:
        return

    def load_config(self, id: int) -> None:
        return

    def save_config(self, id: int) -> None:
        return

    # End of currently tested commands
    # Commands below only return default value to pass Delaygen's
    # ASYN driver's boot-up validity checks
    # without it, the ASYN driver would crash

    def get_prescale_factor(self, which: int) -> str:
        return "0"

    def get_prescale_phase_factor(self, which: int) -> str:
        return "0"

    def get_interface_config(self, which: int) -> str:
        return "0"

    def get_trigger_rate(self) -> str:
        return "0"

    def get_burst_count(self) -> str:
        return "0"

    def get_burst_delay(self) -> str:
        return "0"

    def get_burst_mode(self) -> str:
        return "0"

    def get_burst_period(self) -> str:
        return "0"

    def get_burst_t0(self) -> str:
        return "0"

    def get_holdoff(self) -> str:
        return "0"

    def get_step_size_delay(self, which: int) -> str:
        return "0"

    def get_advanced_triggering_mode(self) -> str:
        return "0"

    def get_inhibit(self) -> str:
        return "0"

    def get_ethernet_mac(self) -> str:
        return "0"
