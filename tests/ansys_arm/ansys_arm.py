"""
Prepare the log file for the Ansys ARM environment.
"""


def write_arm_log(testlog_file, test_id, test_name, test_passed):
    if test_passed:
        test_result = "PASSED"
    else:
        test_result = "FAILED"
    test_log = '<SCENARIO ID="{}" DESC="{}">\n<RESULT>{}</RESULT>\n' "<ARM_JOURNAL_COMPLETE />\n</SCENARIO>\n".format(
        test_id, test_name, test_result
    )
    with open(testlog_file, "a") as file:
        file.write(test_log)
        file.close()
    return test_log
