import sys
import logging

from .test_base import TestBase
import cmd_builder

logging.basicConfig(stream=sys.stderr, level=logging.FATAL)


def empty_function():
    print('empty function')
    pass


class TestFunction(TestBase):

    def test_function(self):
        cmds = [cmd_builder.CmdObject.from_(empty_function)]
        output = self.get_cmd_run_out_put(cmds,"empty_function --help")
        print(output, file=sys.stderr)
        pass
