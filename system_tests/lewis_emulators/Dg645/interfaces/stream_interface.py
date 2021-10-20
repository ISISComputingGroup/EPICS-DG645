from lewis.adapters.stream import StreamInterface, Cmd
from lewis.utils.command_builder import CmdBuilder
from lewis.core.logging import has_log
from lewis.utils.replies import conditional_reply
import queue
import timeit


@has_log
class Dg645StreamInterface(StreamInterface):
    commands = {
        # Commands implemented only for testing the IOC. Does not cover entire functionality of the device
        CmdBuilder("get_ident").escape("*IDN?").eos().build(),
        CmdBuilder("get_delay").escape("DLAY?").spaces().int().eos().build(),
        CmdBuilder("set_delay").escape("DLAY").spaces().int().optional(",").spaces().int().optional(
            ",").spaces().any().eos().build(),
        CmdBuilder("get_trigger_source").escape("TSRC?").eos().build(),
        CmdBuilder("set_trigger_source").escape("TSRC").spaces().int().eos().build(),
        CmdBuilder("get_level_amplitude").escape("LAMP?").spaces().int().eos().build(),
        CmdBuilder("set_level_amplitude").escape("LAMP").spaces().spaces().int().optional(
            ",").spaces().any().eos().build(),
        CmdBuilder("get_level_offset").escape("LOFF?").spaces().int().eos().build(),
        CmdBuilder("set_level_offset").escape("LOFF").spaces().spaces().int().optional(
            ",").spaces().any().eos().build(),
        CmdBuilder("get_level_polarity").escape("LPOL?").spaces().int().eos().build(),
        CmdBuilder("set_level_polarity").escape("LPOL").spaces().int().optional(",").spaces().any().eos().build(),
        CmdBuilder("get_last_error").escape("LERR?").eos().build(),
        CmdBuilder("set_clear_queue").escape("*CLS").eos().build(),
        CmdBuilder("get_trigger_level").escape("TLVL?").eos().build(),
        CmdBuilder("set_trigger_level").escape("TLVL").spaces().any().eos().build(),
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

    def check_int(self, val):
        try:
            int(val)
            return True
        except:
            return False

    def check_float(val):
        try:
            float(val)
            return True
        except:
            return False

    def handle_error(self, request, error):
        self.log.error("An error occurred at request " + repr(request) + ": " + repr(error))

    def catch_all(self, command):
        pass

    def get_ident(self):
        return self._device.identification

    def get_delay(self, which):
        self._device.update_trigger_delays()
        return str(self._device.delays[which][0]) + ',' + str("{:.12f}".format(float(self._device.delays[which][1])))

    def set_delay(self, which, target, amount):
        if which == target or which == 0 or which == 1 or target == 1:
            self._device.add_error(13)  # Illegal link error
            return

        # check if value is a float
        # the device rounds picoseconds to 5, 10, 15 etc
        new_delay = "{:.12f}".format(float(amount))
        new_delay = float(new_delay) * 1e12
        new_delay = 5 * round(new_delay / 5)
        new_delay *= 1e-12
        self._device.delays[which] = (target, new_delay)
        self._device.update_trigger_delays()

    def get_trigger_source(self):
        return self._device.trigger_source

    def set_trigger_source(self, new):
        if new < 0 or new > 6 or not self.check_int(new):
            self._device.add_error(10)  # Illegal value error
        self._device.trigger_source = new

    def get_level_amplitude(self, which):
        return self._device.level_amplitude[which]

    def set_level_amplitude(self, which, new):
        self._device.level_amplitude[which] = new

    def get_level_offset(self, which):
        return self._device.level_offset[which]

    def set_level_offset(self, which, new):
        self._device.level_offset[which] = new

    def get_level_polarity(self, which):
        return self._device.level_polarity[which]

    def set_level_polarity(self, which, new):
        self._device.level_polarity[which] = new

    def get_last_error(self):
        return self._device.get_error()

    def set_clear_queue(self):
        self._device.error_queue = []

    def get_trigger_level(self):
        return self._device.trigger_level

    def set_trigger_level(self, new):
        self._device.trigger_level = new

    # End of currently tested commands

    def get_prescale_factor(self, which):
        return "0"

    def get_prescale_phase_factor(self, which):
        return "0"

    def get_interface_config(self, which):
        return "0"

    def get_trigger_rate(self):
        return "0"

    def get_burst_count(self):
        return "0"

    def get_burst_delay(self):
        return "0"

    def get_burst_mode(self):
        return "0"

    def get_burst_period(self):
        return "0"

    def get_burst_t0(self):
        return "0"

    def get_holdoff(self):
        return "0"

    def get_step_size_delay(self, which):
        return "0"

    def get_advanced_triggering_mode(self):
        return "0"

    def get_inhibit(self):
        return "0"

    def get_ethernet_mac(self):
        return "0"
