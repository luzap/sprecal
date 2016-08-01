from configparser import ConfigParser, ExtendedInterpolation
import sys


def load_setting(section, name):
    config = ConfigParser()
    config._interpolation = ExtendedInterpolation()
    config.read("config.ini")
    name = config.get(section, name)
    return name


def get_platform():
    return sys.platform
