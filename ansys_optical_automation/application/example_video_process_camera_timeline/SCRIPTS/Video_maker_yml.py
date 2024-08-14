# # (c) 2024 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited. ANSYS Confidential Information
#
# '''
# THIS ANSYS SOFTWARE PRODUCT AND PROGRAM DOCUMENTATION INCLUDE TRADE SECRETS AND ARE CONFIDENTIAL AND
# PROPRIETARY PRODUCTS OF ANSYS, INC., ITS SUBSIDIARIES, OR LICENSORS.  The software products and documentation
# are furnished by ANSYS, Inc., its subsidiaries, or affiliates under a software license agreement that contains
# provisions concerning non-disclosure, copying, length and nature of use, compliance with exporting laws, warranties,
# disclaimers, limitations of liability, and remedies, and other provisions.  The software products and documentation
# may be used, disclosed, transferred, or copied only in accordance with the terms and conditions of that software
# license agreement.
# '''

import os
import sys

import cv2


def Get_yml_file():
    yml_path = sys.argv[1]
    return yml_path


def extract_parameters_from_yml(yml_path):
    param = {}  # Dictionary to store parameter chains
    try:
        with open(yml_path, "r") as file:
            for line in file:
                if ":" in line:  # Checking if the line contains ":"
                    key, value = line.split(":", 1)  # Splitting line into key and value
                    key = key.strip()  # Removing leading and trailing whitespace from key
                    value = value.strip()  # Removing leading and trailing whitespace from value
                    if key in param:  # Check if the key already exists in the dictionary
                        if isinstance(param[key], list):  # If the value is already a list
                            param[key].append(value)  # Append value to the list
                        else:  # If the value is not a list, convert it to a list
                            param[key] = [parameters[key], value]
                    else:  # If the key doesn't exist, create a new key-value pair
                        param[key] = value
    except IOError:
        print("Error: File not found or could not be opened.")
    return param


yml_path = Get_yml_file()
param = extract_parameters_from_yml(yml_path)
workingDirBase = r"" + str(param.get("Working Directory"))

frequency = float(param.get("Frame Per Second"))
time_stamp = 1 / float(frequency)  # s
current_time = 0.0  # s
start_time = float(param.get("Start Time (in s)"))  # s
end_time = float(param.get("End Time (in s)"))  # s
videoName = str(param.get("Title"))
videoFilename = os.path.join(workingDirBase, videoName + ".mp4")
imagesNb = int((end_time - start_time) * frequency)

images = []
for i in range(imagesNb):
    images.append(str(i) + ".png")

frame = cv2.imread(os.path.join(workingDirBase, images[0]))
height, width, layers = frame.shape

fourcc = cv2.VideoWriter_fourcc("m", "p", "4", "v")
video = cv2.VideoWriter(videoFilename, fourcc, frequency, (width, height))


for image in images:
    input = cv2.imread(os.path.join(workingDirBase, image))
    video.write(input)

cv2.destroyAllWindows()
video.release()
