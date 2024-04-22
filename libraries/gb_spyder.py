# -*- coding: utf-8 -*-
"""
Created on Thu Nov 29 14:12:10 2018

@author: spau4795
"""
## modified by RK Apr 17. To retrieve original, rename this to something else, and rename "gb - Copy.py" to "gb.py"

from time import sleep

#import sys
#sys.path.append('/Users/LD2007/Documents/qcodes_measurements')

from qcodes.instrument.base import InstrumentBase
from qcodes.instrument.parameter import Parameter
from qcodes.instrument.channel import ChannelList
from qcodes_measurements.device import GateWrapper, DigitalDevice, Register

def isleep(time):
    for i in range(int(time)):
        sleep(1)
    sleep(time - int(time))

class GooseberryWrappedGate(Parameter):
    def __init__(self, name, instrument, gooseberry_gate=None, voltage_source=None, settling_delay=30, **kwargs):
        # Set some default parameters
        if "label" not in kwargs:
            kwargs["label"] = name
        if "unit" not in kwargs:
            kwargs["unit"] = voltage_source.unit
        if "vals" not in kwargs:
            kwargs["vals"] = voltage_source.vals

        # Store instance variables
        self.gooseberry_gate = gooseberry_gate
        self.voltage_source = voltage_source
        self.settling_delay = settling_delay

        # Store last saved voltage
        self.last_voltage = None

        # Initialize the parameter
        super().__init__(name, instrument, **kwargs)

    # Overwrite the default getter and setter
    def get_raw(self): # pylint: disable=method-hidden
        return self.last_voltage

    # modified by RK Apr 17 to include handling of "a gate" that is actually a cluser of gates
    def set_raw(self, value): # pylint: disable=method-hidden
        if type(self.gooseberry_gate) is tuple: # then this gb-gate is a cluster of gates
            if (self.root_instrument.enabled_gate() is None) or (type(self.root_instrument.enabled_gate()) is int) or (sorted(self.root_instrument.enabled_gate()) != sorted(self.gooseberry_gate)): # then these gates are not already enabled (exclusively)
                enable_val = 0
                for i in self.gooseberry_gate:
                    enable_val = enable_val + (1 << i)
                self.root_instrument.registers["CLEN"]["CLEN"] = enable_val
                self.root_instrument.write_spi(self.root_instrument.registers["CLEN"])
                self.voltage_source(value)
                isleep(self.settling_delay)
        elif self.root_instrument.enabled_gate() != self.gooseberry_gate: # then this is a regular single gb-gate that hasn't been enabled
            self.root_instrument.enable_gate(self.gooseberry_gate)
            self.voltage_source(value)
            isleep(self.settling_delay)

        self.voltage_source(value)
        self.last_voltage = value


class Gooseberry(InstrumentBase):
    """
    Gooseberry device that wraps up control of the gooseberry device and keeps
    track of state.

    Args:
        gb_device (DigitalDevice): base gooseberry device, defined as a DigitalDevice
    """
    def __init__(self, gb_device):
        """
        Create a new instance of a gooseberry device.
        """
        super().__init__("Gooseberry")

        # Check we've been given a valid gooseberry device
        if not isinstance(gb_device, DigitalDevice) or not hasattr(gb_device, "SPI"):
            raise TypeError("gb_device must be a DigitalDevice with an SPI interface")
        self.gb = gb_device

        # Add Register Definitions
        # pylint: disable=bad-whitespace
        self.registers = {}
        self.registers["IOCTL"] =   Register("IOCTL", 0x04, (("DRIVE", 0, 2),),
                                             require_sync=True)
        self.registers["DBGCTL"] =  Register("DBGCTL", 0x08, (("DTEST1_MUX", 0, 2),
                                                              ("DTEST2_MUX", 3, 5)),
                                             require_sync=True)
        self.registers["CTL1"] =    Register("CTL1", 0x0C, (("EN_SEL", 0, 0),
                                                            ("XCLK_DIS", 1, 1),
                                                            ("FG_SEL", 2, 3),
                                                            ("BEGIN_CHRG", 4, 5),
                                                            ("CHRG_SEL", 6, 7),
                                                            ("FGSR_EN", 8, 8)),
                                             require_sync=True)
        self.registers["CLEN"] =    Register("CLEN", 0x10, (("CLEN", 0, 31),), require_sync=True)
        self.registers["CLMODE"] =  Register("CLMODE", 0x14, (("CLMODE", 0, 15),), require_sync=True)
        self.registers["TST"] =     Register("TST", 0x18, (("TST", 0, 31),), require_sync=True)
        self.registers["DCSR"] =    Register("DCSR", 0x1C, (("DCSR", 0, 15),), require_sync=True)
        self.registers["CLKCTL"] =  Register("CLKCTL", 0x20, (("FDIV", 0, 7),
                                                              ("OSC_SEL", 8, 8),
                                                              ("OSC_TRIM", 9, 16),
                                                              ("OSC_EN", 17, 17)),
                                             require_sync=True)
        self.registers["FGSR"] =    Register("FGSR", 0x24, (("FGSR", 0, 127),), length=128, require_sync=True)
        # RK adding the below, 10-Apr-2019
        self.registers["FGSR0"] =    Register("FGSR0", 0x24, (("FGSR0", 0, 31),), require_sync=True)
        self.registers["FGSR1"] =    Register("FGSR1", 0x28, (("FGSR1", 0, 31),), require_sync=True)
        self.registers["FGSR2"] =    Register("FGSR2", 0x2C, (("FGSR2", 0, 31),), require_sync=True)
        self.registers["FGSR3"] =    Register("FGSR3", 0x30, (("FGSR3", 0, 31),), require_sync=True)

        # Define Register Constants
        self.registers["DBGCTL"].APBCLK = 0
        self.registers["DBGCTL"].SCLK = 1
        self.registers["DBGCTL"].APBCTL_NEWREQ = 2
        self.registers["DBGCTL"].OSCCLK = 3
        self.registers["DBGCTL"].CLCLK_OUT = 4
        self.registers["DBGCTL"].CLFG = 5
        self.registers["DBGCTL"].CLCHRG = 6
        self.registers["DBGCTL"].FSM_IDLEB1 = 7

        # Create a map to gooseberry parameters
        self.parameters = self.gb.parameters.copy()
        self.add_submodule("gates", self.gb.gates)
        self.add_submodule("digital_gates", self.gb.digital_gates)

        # Create some convenient channel lists
        self.bgs = ChannelList(self, "backgates", GateWrapper)
        for gate in ("BGN1P8", "BGP1P8", "BGN1P0", "BGP1P0"):
            self.bgs.append(getattr(self.gb.gates, gate))
        self.bgs.lock()

        # And some instance variables
        self.manual_clk = False # Set to true if we are controlling the clock ourselves

    def add_chargelocked_gate(self, name, gooseberry_gate, **kwargs):
        """
        Add a gate connected to gooseberry.
        """
        self.add_parameter(name,
                           parameter_class=GooseberryWrappedGate,
                           gooseberry_gate=gooseberry_gate,
                           voltage_source=self.gb.VICL,
                           **kwargs)

    def power_up(self, vdd1p0=1):
        """
        Power up gooseberry using values set for v_high and v_low
        """
        v_high = self.gb.v_high()
        v_low = self.gb.v_low()

        # Set TMODE
        self.gb.TMODE(0) # - no TMODE in XLD experiment
        # Start with ground and VDD1P0 domian
        self.gb.VSS1P8(v_low)
        self.gb.VDD1P0(v_low)
        # Set with backgates
        self.bgs.voltage(v_low)
        
        # Set 1.8V Rail
        self.gb.VDD1P8(v_high)
        self.gb.VDD1P8_ANA(v_high)

        #self.gb.VSS1P0(v_low)
        # Now Set 1V Rail
        self.gb.VDD1P0(v_low+vdd1p0)


        # Reset gooseberry
        #self.reset()
        self._hard_reset_gb()

    def startup(self):
        """
        Set gooseberry registers to operating values
        """
        self.registers["DBGCTL"]["DTEST1_MUX"] = self.registers["DBGCTL"].FSM_IDLEB1
        self.registers["DBGCTL"]["DTEST2_MUX"] = self.registers["DBGCTL"].FSM_IDLEB1
        self.registers["CTL1"]["EN_SEL"] = 1
        self.registers["CTL1"]["XCLK_DIS"] = 1
        self.registers["CTL1"]["FG_SEL"] = 0x1
        self.registers["CTL1"]["BEGIN_CHRG"] = 0
        self.registers["CTL1"]["CHRG_SEL"] = 0x3
        self.write_registers(self.registers["DBGCTL"],
                             self.registers["CTL1"],
                             self.registers["CLMODE"])

    def _hard_reset_gb(self):
        self.gb.RST_N(0)
        self.gb.RST_N(1)

    def reset(self):
        """
        Toggle reset pin and set registers to known startup values
        """
        # Toggle reset pin and start up gooseberry
        self._hard_reset_gb()

        # Set default register states
        self.registers["IOCTL"][:] = 7
        self.registers["DBGCTL"][:] = 0
        self.registers["CTL1"][:] = 0
        self.registers["CLEN"][:] = 0
        self.registers["CLMODE"][:] = 0
        self.registers["TST"][:] = 0
        self.registers["DCSR"][:] = 0
        self.registers["CLKCTL"][:] = 0
        self.registers["FGSR"][:] = 0
        for register in self.registers.values():
            register.commit()
        # Startup
        self.startup()

    def power_down(self):
        """
        Set all gooseberry gates to 0V
        """

        self.gb.digital_gates.voltage(0)
        self.gb.gates.voltage(0)

    def start_clk(self):
        """
        Start APBCLK
        """
        amplitude = abs(self.gb.v_high() - self.gb.v_low())
        offset = (self.gb.v_high() + self.gb.v_low())/2
        self.gb.APBCLK.source.awg_square(1000, amplitude, offset)

    def stop_clk(self):
        """
        Stop APBCLK
        """
        self.gb.APBCLK(0)

    def write_registers(self, *registers):
        """
        Write out multiple registers at once. This prevents APBCLK from
        toggling on and off, making the process a bit faster.
        """
        restore = self.manual_clk
        if not self.manual_clk:
            self.start_clk()
            self.manual_clk = True

        for register in registers:
            self.write_spi(register)

        self.manual_clk = restore
        if not self.manual_clk:
            self.stop_clk()

    def write_spi(self, register):
        """
        Write a register out via SPI. This commits the value in the register
        """
        if not self.manual_clk:
            self.start_clk()

        preamble = bytes((0x00, 0x00, 0xF0, register.address))
        self.gb.SPI.transfer_bytes(preamble + bytes(register))
        register.commit()

        if not self.manual_clk:
            self.stop_clk()

    def enabled_gate(self):
        """
        Return the currently enabled gate, None if no gates are enabled,
        and a tuple of gates if multiple are enabled.
        """
        if self.registers["CLEN"].committed_val is None:
            return None
        val = f'{self.registers["CLEN"].committed_val:032b}'
        n_enabled = val.count("1")
        if n_enabled == 0:
            return None
        if n_enabled == 1:
            return 31 - val.index('1')
        return tuple(31-i for i, b in enumerate(val) if b=='1')

    def enable_multiple_gates(self, gates):
        val = 0
        for g in gates:
            val |= (1 << g)
        self.registers["CLEN"]["CLEN"] = val
        self.write_registers(self.registers["CLEN"])

    def enable_gate(self, gate):
        """
        Enable a single gooseberry gate
        """
        self.registers["CLEN"]["CLEN"] = (1 << gate)
        self.write_spi(self.registers["CLEN"])

    def enable_not_gate(self, gate):
        """
        Enable all gates except for one
        """
        self.registers["CLEN"]["CLEN"] = (1<<gate) ^ (0xFFFFFFFF)
        self.write_spi(self.registers["CLEN"])

    def enable_atest(self, gate):
        """
        Enable ATEST on a gooseberry gate
        """
        self.registers["TST"]["TST"] = (1<<gate)
        self.write_spi(self.registers["TST"])

    def disable_all_gates(self):
        """
        Close all gooseberry gates
        """
        self.registers["CLEN"]["CLEN"] = 0
        self.write_spi(self.registers["CLEN"])

    def set_clk(self, fdiv=255, osc_sel=1, osc_trim=1, osc_en=1):
        """
        Set the internal gooseberry oscillator state
        """
        if osc_en == 1:
            if bin(osc_trim).count("1") != 1:
                raise ValueError("OSC_TRIM must have a single bit set")
        else:
            if osc_trim != 0:
                raise ValueError("OSC_TRIM must be 0 if OSC_EN if disabled")
        self.registers["CLKCTL"]["FDIV"] = fdiv
        self.registers["CLKCTL"]["OSC_SEL"] = osc_sel
        self.registers["CLKCTL"]["OSC_TRIM"] = osc_trim
        self.registers["CLKCTL"]["OSC_EN"] = osc_en
        self.write_spi(self.registers["CLKCTL"])

    def snapshot_base(self, update=False, params_to_skip_update=None):
        """
        Overwrite snapshot_base to store registers
        """
        snap = super().snapshot_base(update)
        snap["registers"] = {register.name: register.snapshot() for register in self.registers.values()}
        return snap
