# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 11:48 2024

Wrapper class for the SHFQC device to make connections easy.

@author: james
"""

from zhinst.toolkit import Session, CommandTable


class SHFQC:
    """Connect and control the SHFQC device."""
    def __init__(self,
                 sg_channels: list[str],
                 sg_addresses: list[int],
                 qa_channel_name: str,
                 device_id: str = "DEV12158",
                 server_host: str = "localhost",
                 ):
        """
        Configure the device
        Args:
            sg_channels: ["ST", "P1", "P2", ...] is a list of the channels
            sg_addresses: [0, 3, 2, ...] is a list of which output to assign for each channel
            qa_channel_name: Name for the QA channel
        """
        self.session = Session(server_host)
        self.device_id = device_id
        self.device = None
        self.sg_channel_names = sg_channels
        self.drive_channels = sg_channels  # assume all sg channels are driven
        self.sg_addresses = sg_addresses
        self.qa_channel_name = qa_channel_name
        self.cmd_tables = {}

    def connect(self):
        """Connect to the device through the current session"""
        print(f"Connecting to device {self.device_id}")
        self.device = self.session.connect_device(self.device_id)

        # Setup channels for easy access eg `shfqc.st`
        self.__dict__[self.qa_channel_name] = self.device.qachannels[0]
        for (name, address) in zip(self.sg_channel_names, self.sg_addresses):
            if 0 <= address < 6:
                self.__dict__[name] = self.device.sgchannels[address]
            else:
                raise ValueError(f"Channel address {address} out of range")
        self.create_command_tables()

    def create_command_tables(self):
        """Create base command tables to easily modify in the future."""
        print("Creating new command tables")
        self.cmd_tables = {
            c: CommandTable(self.__dict__[c].awg.commandtable.load_validation_schema())
            for c in self.drive_channels
        }

    def disconnect(self):
        """Disconnect to the device."""
        print(f"Disconnecting from device {self.device_id}")
        self.session.disconnect_device(self.device_id)
        self.device = None

    def __getitem__(self, item):
        return getattr(self, item)  # wraps dictionary querying to attributes

    def __setitem__(self, key, value):
        raise KeyError("These values are immutable.")

    def desync(self):
        """Descync all channels. Otherwise some measurements never start..."""
        for i in range(6):
            self.device.sgchannels[i].synchronization.enable(0)
        self.device.system.internaltrigger.synchronization.enable(0)
        self.device.qachannels[0].synchronization.enable(0)

    def reset(self):
        """
        Reset the device.
            - Clear all sequencer programs
            - Disable all outputs
        """
        pass