from pyflipper.pyflipper import PyFlipper
from typing import Dict


class IR:
    def __init__(self, name_, type_, protocol_=None, address_=None, command_=None):
        def reverse_address_or_cmd(data_str: str) -> str:
            return ''.join(data_str.split()[::-1])

        self.name = name_
        self.type = type_
        self.protocol = protocol_
        self.address = reverse_address_or_cmd(address_) if address_ else None
        self.command = reverse_address_or_cmd(command_) if command_ else None

    def __str__(self):
        return f"{self.name}({self.protocol}) ADDR: {self.address} CMD: {self.command}"


def decode_ir_file(data):
    removed = data.split("#")[1:]
    result = {}
    for elem in removed:
        template = {"name_": None, "type_": None, "protocol_": None, "address_": None, "command_": None}
        for part in elem.strip().split("\n"):
            key, value = part.split(":")
            template[f"{key.strip()}_"] = value.strip()
        result[template["name_"]] = IR(**template)

    return result


def get_list_of_ir(flipper_device: PyFlipper):
    return [elem["name"] for elem in flipper_device.storage.list(path="/ext/infrared").get('files')]


def get_device_name(flipper_device: PyFlipper):
    return flipper_device.device_info.info().get("hardware_name")


def get_ir_file_data(flipper_device: PyFlipper, file_name: str):
    filepath = f"/ext/infrared/{file_name}"
    return flipper_device.storage.read(file=filepath)


def send_ir_command(flipper_device: PyFlipper, remotes: Dict, command_name: str):
    command = remotes.get(command_name)
    if command:
        flipper_device.ir.tx(command.protocol, command.address, command.command)


if __name__ == "__main__":
    pass
