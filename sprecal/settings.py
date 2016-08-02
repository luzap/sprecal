import sys
import os
import winreg
from configparser import ConfigParser, ExtendedInterpolation

STARTUP_DIR = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"


def get_key_params(filename):
    return (filename.split("\\")[-1].split(".")[0].title(),
            os.path.join(os.path.abspath(os.path.curdir), filename))


def set_key(name, value):
    try:
        # winreg.CreateKey(winreg.HKEY_CURRENT_USER, STARTUP_DIR)
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_DIR, 0,
                            winreg.KEY_WRITE)
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
        winreg.CloseKey(key)
        return True
    except (WindowsError, OSError) as ex:
        return False


def load_setting(section, name):
    config = ConfigParser()
    config._interpolation = ExtendedInterpolation()
    config.read("config.ini")
    name = config.get(section, name)
    return name


def get_platform():
    return sys.platform
