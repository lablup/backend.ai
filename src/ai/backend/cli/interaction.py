import ipaddress
from pathlib import Path
from typing import Optional, Union
from urllib.error import HTTPError
from urllib.request import urlopen

Numeric = Union[int, float]


def ask_host(prompt: str, default: str = "127.0.0.1", allow_hostname=False) -> str:
    while True:
        user_reply = input(f"{prompt} (default: {default}): ")
        if user_reply == "":
            user_reply = default
        try:
            if allow_hostname:
                url = user_reply
                if not (user_reply.startswith("http://") or user_reply.startswith("https://")):
                    url = f"http://{user_reply}"
                try:
                    urlopen(url)
                    break
                except HTTPError:
                    print("Please input correct URL.")
            ipaddress.ip_address(user_reply)
            break
        except ValueError:
            print("Please input correct host.")
    return user_reply


def convert_str_into_numeric(user_reply: str) -> Numeric:
    if user_reply.isdigit():
        return int(user_reply)
    return float(user_reply)


def ask_number(prompt: str, default: Numeric, min_value: Numeric, max_value: Numeric) -> Numeric:
    while True:
        user_reply = input(f"{prompt} (default: {default}): ")
        try:
            if user_reply == "":
                return default
            if (
                user_reply.isdigit()
                and min_value <= convert_str_into_numeric(user_reply) <= max_value
            ):
                user_reply_numeric = convert_str_into_numeric(user_reply)
                break
        except ValueError:
            print(f"Please input correct number between {min_value}~{max_value}.")
    return user_reply_numeric


def ask_string(prompt: str, default: str = "", use_default: bool = True) -> str:
    while True:
        if use_default:
            user_reply = input(f'{prompt} (default: "{default}"): ')
            if user_reply == "":
                return default
            return user_reply
        else:
            user_reply = input(f"{prompt} (if you don't want, just leave empty): ")
            return user_reply


def ask_string_in_array(prompt: str, choices: list, default: str) -> Optional[str]:
    if default and default not in choices:
        print("Default value should be in choices args.")
        return None
    if "" in choices:
        choices.remove("")

    if default:
        question = (
            f"{prompt} (choices: {'/'.join(choices)}, "
            f"if left empty, this will use default value: {default}): "
        )
    else:
        question = (
            f"{prompt} (choices: {'/'.join(choices)}, if left empty, this will remove this key): "
        )

    while True:
        user_reply = input(question)
        if user_reply == "":
            if default:
                user_reply = default
            else:
                return None
            break
        elif user_reply.lower() in choices:
            break
        else:
            print(f"Please answer in {'/'.join(choices)}.")
    return user_reply


def ask_path(prompt: str, is_file=True, is_directory=True) -> Path:
    if not (is_file or is_directory):
        print("One of args(is_file/is_directory) has True value.")
    while True:
        user_reply = input(f"{prompt}: ")
        path = Path(user_reply)
        if is_file and path.is_file():
            break
        if is_directory and path.is_dir():
            break

        if is_file and is_directory:
            print("Please answer a correct file/directory path.")
        elif is_file:
            print("Please answer a correct file path.")
        elif is_directory:
            print("Please answer a correct directory path.")
    return path


def ask_yn(prompt: str = "Are you sure?", default: str = "y") -> bool:
    if default == "y":
        choices = "Y/n"
    elif default == "n":
        choices = "y/N"
    else:
        raise ValueError("default must be given either 'y' or 'n'.")
    while True:
        user_reply = input("{0} [{1}] ".format(prompt, choices)).lower()
        if user_reply == "":
            user_reply = default
        if user_reply in ("y", "yes", "n", "no"):
            break
        else:
            print("Please answer in y/yes/n/no.")
    if user_reply[:1].lower() == "y":
        return True
    return False


def ask_tf(prompt: str = "Are you sure?", default: str = "true") -> bool:
    if default == "t":
        choices = "T/f"
    elif default == "f":
        choices = "t/F"
    else:
        raise ValueError("default must be given either 'true' or 'n'.")
    while True:
        user_reply = input(f"{prompt} [{choices}] ").lower()
        if user_reply == "":
            user_reply = default
        if user_reply in ("t", "true", "f", "false"):
            break
        else:
            print("Please answer in t/true/f/false.")
    if user_reply[:1].lower() == "t":
        return True
    return False
