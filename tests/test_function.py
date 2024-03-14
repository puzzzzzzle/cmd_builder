import sys
import logging

from .test_base import TestBase
import cmd_builder

logging.basicConfig(stream=sys.stderr, level=logging.FATAL)


def print_error(msg):
    print(msg, file=sys.stderr)


def empty_function():
    """
    empty function's help message
    :return:
    """
    print('empty function')


def func_with_args(flag: bool, arg1, arg2: int, arg3="sss"):
    """
    func_with_args's help msg.
    has multi line.
    :param flag:  flag arg's help message
    :param arg1: arg1 arg's help message
    :param arg2: arg2 arg's help message
    :param arg3: arg3 arg's help message
    :return:
    """
    print('func_with_args', flag, arg1, arg2, arg3)


class TestFunction(TestBase):
    def test_function(self):
        cmds = [cmd_builder.CmdObject.from_(empty_function), cmd_builder.CmdObject.from_(func_with_args)]

        output = self.get_cmd_run_out_put(cmds, args="")
        print_error(output)
        pass
