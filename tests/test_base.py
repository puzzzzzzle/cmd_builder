import argparse
import io
import sys
import unittest

import cmd_builder


class TestableArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)

    # 重写exit方法来抛出异常
    def exit(self, status=0, message=None):
        if status == 0:
            return
        else:
            # 错误码非0, 抛出异常模拟错误
            raise RuntimeError(f" status : {status} : {message}")


class TestBase(unittest.TestCase):
    def setUp(self):
        self.held_output = None
        self.old_output = None

    def tearDown(self):
        self.restore_out_put()

    def hook_new_out_put(self):
        if self.old_output is None:
            self.old_output = sys.stdout
        self.held_output = io.StringIO()
        sys.stdout = self.held_output

    def restore_out_put(self):
        if self.old_output is not None:
            sys.stdout = self.old_output
            self.old_output = None
            self.held_output = None

    @property
    def out_put(self):
        return self.held_output.getvalue()

    def get_cmd_run_out_put(self, cmds, args: str):
        self.hook_new_out_put()
        arg_list = [x for x in args.split(" ") if x != ""]
        cmd_builder.cmd_main(cmds, arg_list, TestableArgumentParser)
        stdout = self.out_put
        self.restore_out_put()
        return stdout
