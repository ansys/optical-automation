from opcode import stack_effect
import os
import tkinter as tk
from tkinter import filedialog

from ansys_optical_automation.post_process.dpf_stack import DpfStack


def getfilename(extension, save=False):
    """
    Parameters
    ----------
    extension : str
        containing the which file extension in *.ending format
    save : Bool
        option to define to open(default) or save. The default is False.

    Returns
    -------
    str
        string containing the selected file path
    """
    root = tk.Tk()
    root.withdraw()
    if not save:
        file_path = filedialog.askopenfilename(filetypes=[("Stack data", extension)])
    else:
        file_path = filedialog.asksaveasfilename(filetypes=[("Stack data", extension)])
        if not file_path.endswith(extension.strip("*")):
            file_path += extension.strip("*")
    return file_path


def main():
    stack_test_version = 222
    stack_result_file = getfilename("*.ldf")
    if not stack_result_file:
        print("Exit programme, you have not select any files")
        return
    stack_dpf = DpfStack(stack_test_version)
    stack_dpf.open_file(stack_result_file)
    stack_dpf.convert_stack_to_speos()
    print("Success: conversion of stack to Speos coating is done")

main()

