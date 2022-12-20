#!/usr/bin/env python3
import gatt
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gatt-exec-server")

CONFIG_FILE = "/data/setupOptions/gatt-exec-server/config.json"


def create_uuid(uuid16):
    return f"0000{uuid16}-25c4-4df6-b81a-f5b3ed6ec59d"


class ExecApplication(gatt.Application):
    def __init__(self, bus, config):
        super().__init__(bus)
        self.add_service(ExecService('/org/bluez/service/exec', bus, config))

    def __str__(self):
        return "exec"


class ExecService(gatt.Service):
    UUID = create_uuid("9200")

    def __init__(self, path, bus, config):
        super().__init__(path, bus, ExecService.UUID, True)
        self.config = config
        self.add_characteristic(ExecCharacteristic('characteristic/exec', bus, self))


class ExecCharacteristic(gatt.Characteristic):
    UUID = create_uuid("9210")

    def __init__(self, path, bus, service):
        super().__init__(path, bus, ExecCharacteristic.UUID, ['write'], service)

    def WriteValue(self, value, options):
        operation = bytes(value).decode('utf-8')
        name_args = operation.split(':', 1)
        cmd_template = self.service.config.get(name_args[0])
        if cmd_template is not None:
            if len(name_args) > 1:
                command = cmd_template.format(name_args[1].split(' '))
            else:
                command = cmd_template
            logger.info(f"Received operation '{operation}' - running command '{command}'")
            os.system(command)


def main():
    with open(CONFIG_FILE) as f:
        config = json.load(f)

    DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    service_manager = gatt.get_service_manager(bus)
    app = ExecApplication(bus, config)
    mainloop = GLib.MainLoop()
    def on_registration_success():
        logger.info(f"Successfully registered {app} application")
    def on_registration_error(error):
        logger.error(f"Failed to register {app} application: {error}")
        mainloop.quit()
    service_manager.RegisterApplication(app.get_path(), {},
        reply_handler=on_registration_success,
        error_handler=on_registration_error)
    mainloop.run()


if __name__ == "__main__":
    main()
