import argparse
import functools
import inspect
import re
import logging
import types

logger = logging.getLogger(__name__)


class CmdObject(object):
    """
    This class is responsible for holding the information of building one command
    """

    def __init__(self, cmd_code, cmd_name: str, description: str, help_str: str, target_obj=None):
        cmd_name = cmd_name or cmd_code.__name__
        description = description or get_func_doc(cmd_code)
        help_str = help_str or description

        self.cmd_name = cmd_name
        self.cmd_code = cmd_code
        self.description = description
        self.help_str = help_str
        self.target_obj = target_obj
        self.annotations = None
        self.default_args = None
        self.normal_args = None

    @property
    def is_class_func(self):
        return self.target_obj is not None

    @staticmethod
    def from_function(function, cmd_name=None, description=None, help_str=None):
        return CmdObject(function, cmd_name, description, help_str, None)

    @staticmethod
    def from_method(class_obj, method, cmd_name=None, description=None, help_str=None):
        return CmdObject(method, cmd_name, description, help_str, class_obj)

    @staticmethod
    def from_(function, cmd_name=None, description=None, help_str=None):
        if isinstance(function, types.FunctionType):
            return CmdObject.from_function(function, cmd_name, description, help_str)
        elif isinstance(function, types.MethodType):
            return CmdObject.from_method(function.__self__, function, cmd_name, description, help_str)
        return None


def get_func_doc(cmd_code):
    """
    get function's default description and help string
    :param cmd_code:
    :return:
    """
    desc = cmd_code.__doc__ or ''
    result = []
    for line in desc.split('\n'):
        if line.strip() == "":
            continue
        if line.strip().startswith(':param') or line.strip().startswith(':return'):
            break
        result.append(line)
    return "\n".join(result)


def get_param_description(function, para_name):
    """
    get para's comment
    """
    docstring = function.__doc__
    if not docstring:
        return ""

    # regex for para
    pattern = rf":param\s*{para_name}\s*:\s*(.+)\s*"
    regex = re.compile(pattern, re.MULTILINE)
    match = regex.search(docstring)

    if match:
        param_desc = match.groups()
        return f"{param_desc[0]}"
    else:
        return ""


class MyHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    def _format_args(self, action, default_metavar):
        return action.metavar


def build_args(sub_cmds, obj: CmdObject):
    """
    build args for parser by function define
    """
    # add parser
    parser = sub_cmds.add_parser(obj.cmd_name, description=obj.description,
                                 help=obj.help_str, formatter_class=MyHelpFormatter)

    # inspect all args
    cmd_code = obj.cmd_code
    args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations = inspect.getfullargspec(cmd_code)
    default_arg_start = len(args)
    if defaults is not None:
        default_arg_start = len(args) - len(defaults)

    # add args
    normal_args = []
    default_args = {}
    for i in range(len(args)):
        # ignore this
        if i == 0 and obj.is_class_func:
            continue
        arg = args[i]
        # this arg has default value
        if i >= default_arg_start:
            default = defaults[i - default_arg_start]
            default_args[arg] = default
        else:
            normal_args.append(arg)

    # add positional requires args
    obj.normal_args = normal_args
    obj.default_args = default_args
    obj.annotations = annotations
    if len(normal_args) > 0:
        normal_args_help = ""
        metavar_str = ""
        for arg in normal_args:
            metavar_str += f"{arg} "
            t = str
            if arg in annotations:
                t = annotations[arg]
            comment = get_param_description(cmd_code, arg)
            if comment != "":
                comment = ":" + comment
            normal_args_help += f"[{arg}({t.__name__}){comment}] "
        parser.add_argument("args", metavar=metavar_str, type=str, nargs=len(normal_args),
                            help=normal_args_help)

    # add default args
    if len(default_args) > 0:
        for arg, value in default_args.items():
            if arg in annotations:
                t = annotations[arg]
            elif value is not None:
                t = type(value)
            else:
                t = str
            name = f"--{arg}"
            if len(arg) == 1:
                name = f"-{arg}"
            paras = {"type": t, "default": value}
            help_str = f"{get_param_description(cmd_code, arg)}"
            if t == bool:
                del paras["type"]
                if value:
                    help_str += f", default is set, add flags to set false"
                    paras["action"] = "store_false"
                else:
                    help_str += f", default is not set, add flags to set true"
                    paras["action"] = "store_true"

                paras["help"] = help_str
            else:
                paras["help"] = help_str

            parser.add_argument(name, **paras)

    parser.set_defaults(func=functools.partial(run_one_cmd, obj))
    pass


def run_one_cmd(obj: CmdObject, para):
    """
    execute target  func/class
    """
    normal_args = obj.normal_args
    default_args = obj.default_args
    annotations = obj.annotations
    logger.debug(f"run {obj.cmd_name} {para}")
    # normal args
    if len(normal_args) > 0:
        args = list(para.args)
        assert len(args) == len(normal_args)
        for i in range(len(normal_args)):
            arg_name = normal_args[i]
            if arg_name in annotations:
                arg_type = annotations[arg_name]
                logger.debug(f"trans type {arg_name} -> {arg_type}; str value: {args[i]} ")
                args[i] = arg_type(args[i])
        args = tuple(args)
        logger.debug(f"position args {args}")
    else:
        args = ()
    # default args
    if len(default_args) > 0:
        kwargs = dict(default_args)
        for key in default_args.keys():
            attr = getattr(para, key)
            logger.debug(f"get {key} {attr}")
            kwargs[key] = attr
        logger.debug(f"default args {kwargs}")
    else:
        kwargs = {}
    if obj.is_class_func:
        obj.cmd_code(obj.target_obj, *args, **kwargs)
    else:
        obj.cmd_code(*args, **kwargs)
    pass


def cmd_main(cmds: list[CmdObject] = None, args=None, parser=argparse.ArgumentParser, help_str=""):
    """
    main args builder
    :return:
    """
    root = parser(description=help_str)
    root.set_defaults(func=lambda *args: root.print_help())

    sub_cmds = root.add_subparsers(help=f"supported cmds:")
    for cmd in cmds:
        build_args(sub_cmds, cmd)
    args = root.parse_args(args)
    # execute
    args.func(args)

# def empty_function():
#     print('empty function')
#     pass
#
# if __name__ == '__main__':
#     args = "empty_function -h"
#     cmds = [CmdObject.from_(empty_function)]
#     arg_list = [x for x in args.split(" ") if x != ""]
#     cmd_main(cmds, arg_list)
