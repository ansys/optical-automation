import os
import sys

from ansys_optical_automation.post_process.dpf_stack import DpfStack

unittest_path = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.dirname(unittest_path)
sys.path.append(lib_path)


def unittest_run():
    stack_result_file = os.path.join(unittest_path, "example_models", "test_10_stack_interop.ldf")
    action = DpfStack(stack_result_file)
    action.convert_stack_to_speos()
