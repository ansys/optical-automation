import os
import sys

from ansys_optical_automation.post_process.dpf_stack import DpfStack

unittest_path = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.dirname(unittest_path)
sys.path.append(lib_path)


def unittest_run(stack_test_version):
    stack_result_file = os.path.join(unittest_path, "example_models", "test_10_stack_interop.ldf")
    stack_dpf = DpfStack(stack_test_version)
    stack_dpf.open_file(stack_result_file)
    stack_dpf.convert_stack_to_speos()
    stack_dpf.convert_stack_to_zemax()
