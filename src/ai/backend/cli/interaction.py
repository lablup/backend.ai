import functools
import ipaddress
import readline
import socket
from pathlib import Path
from typing import Optional, Sequence, Type, TypeVar, Union, cast

T_Number = TypeVar("T_Number", bound=Union[int, float])


def rl_input(prompt: str, prefill: str = "") -> str:
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()


def ask_host(prompt: str, default: str = "127.0.0.1", allow_hostname=False) -> str:
    prefill = default
    while True:
        user_reply = rl_input(f"{prompt}: ", prefill=prefill)
        if user_reply == "":
            user_reply = default
        try:
            if allow_hostname:
                socket.gethostbyname(user_reply)
            ipaddress.ip_address(user_reply)
            break
        except (socket.gaierror, ValueError):
            print("Please input correct host.")
            prefill = user_reply
    return user_reply


def ask_int(
    prompt: str,
    *,
    default: Optional[int] = None,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
) -> int:
    return ask_number_impl(prompt, int, default=default, min_value=min_value, max_value=max_value)


ask_port = functools.partial(ask_int, min_value=1, max_value=65535)


def ask_float(
    prompt: str,
    *,
    default: Optional[float] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
) -> float:
    return ask_number_impl(prompt, float, default=default, min_value=min_value, max_value=max_value)


def ask_number_impl(
    prompt: str,
    num_type: Type[T_Number],
    *,
    default=None,
    min_value=None,
    max_value=None,
) -> T_Number:
    prefill = "" if default is None else str(default)
    while True:
        user_reply = rl_input(f"{prompt}: ", prefill=prefill)
        if not user_reply:
            if default is not None:
                return default
            else:
                print("You must input the value.")
                continue
        try:
            value = cast(T_Number, num_type(user_reply))
        except ValueError:
            print("Could not parse the input as a number!")
            prefill = user_reply
            continue
        if min_value is not None and min_value > value:
            print(f"The number must be equivalent to or greater than {min_value}.")
            prefill = str(value)
            continue
        if max_value is not None and max_value < value:
            print(f"The number must be equivalent to or less than {max_value}.")
            prefill = str(value)
            continue
        return value


def ask_string(
    prompt: str,
    *,
    default: Optional[str] = None,
    allow_empty: bool = False,
) -> str:
    prefill = "" if default is None else default
    while True:
        if default is not None:
            user_reply = rl_input(f"{prompt}: ", prefill=prefill)
            if not user_reply:
                return default
            return user_reply
        else:
            user_reply = rl_input(f"{prompt} (may be left empty): ", prefill=prefill)
            if not user_reply and not allow_empty:
                print("You must input the value.")
                continue
            return user_reply


def ask_choice(
    prompt: str,
    choices: Sequence[str],
    *,
    default: Optional[str] = None,
    allow_empty: bool = False,
) -> str:
    if default and default not in choices:
        raise ValueError("The default value must be included in the choices.")
    prefill = "" if default is None else default
    if allow_empty:
        prompt = f"{prompt} (choices: {', '.join(choices)}, may be left empty): "
    else:
        prompt = f"{prompt} (choices: {', '.join(choices)}): "
    while True:
        user_reply = rl_input(prompt, prefill=prefill)
        if not user_reply and allow_empty:
            return ""
        if user_reply in choices:
            return user_reply
        print(f"Please answer one of: {', '.join(choices)}.")
        prefill = user_reply


def ask_path(prompt: str, is_file=True, is_directory=True) -> Path:
    # TODO: rewrite using rl_input and proper default values
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
