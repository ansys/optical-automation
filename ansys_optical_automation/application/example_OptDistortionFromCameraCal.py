# generate an OPTDistortionV1 file for Speos, based on a camera calibration of a real camera
# this tool runs the camera calibration with user-provided checkerboard images
#
# required data: 
#   - a set of checkerboard calibration images for a given camera (at least 15-20 is best, taken from different angles and distances)
#   - the checkerboard target feature size (width of a single checker)
#   - the camera's physical pixel size (mm)
#
# outputs:
#   - a txt file describing calibration results (camera intrinsics, and pose for each calibration image)
#   - OPTDistortion v1 file, for use in speos
#
# 2024/4/16
# for questions, contact zach.derocher@ansys.com

import cv2 
import numpy as np 
import os 
import glob 
from scipy.spatial.transform import Rotation  


# ======================== USER INPUTS ======================== #
# point to the calibration images
imageDir = os.getcwd() + '\\CalibrationImages\\'
ext = 'jpg'

# show each image during checkerboard detection? (useful for debugging)
showCalImages = False

# best-guess value for camera EFL (units=pixels); ~1x the sensor resolution X is generally a reasonable guess if you have no idea
efl = 3840
# the physical pixel size for the sensor (need this to convert calibrated distortion into angles for speos)
pixelSize = 0.0021 #mm

# Define the dimensions of checkerboard 
checkerboard = (11,8) # (x, y); the number of points between checkerboard boxes
targetSquareSize = 30 # (mm); the physical, measured side-length of each individual checkerboard box in the calibration pattern

# Choose which calibration type; fisheye will provide a better fit if the camera is wide-FOV (beyond 100~120)
useFisheyeCalibration = False

extrinsicsFn = "CameraCal_IntrinsicsExtrinsics.txt"
optDistortionFn = "CameraCal.OPTDistortion"
# ============================================================ #


def buildinitialcameramatrix(efl, rX, rY):
    cameraMat = np.zeros((3, 3), np.float64)
    cameraMat[0, 0] = efl # camera focal length X (units=pixels); the calibration will use this as a starting point; 
    cameraMat[1, 1] = efl # camera focal length Y (units=pixels)
    cameraMat[2, 2] = 1 # skew factor (probably always stay as 1)
    cameraMat[0, 2] = 0.5 * rX # image center coordinates X (units=pixels); this should be set to 1/2 the sensor X resolution
    cameraMat[1, 2] = 0.5 * rY # image center coordinates Y (units=pixels); this should be set to 1/2 the sensor Y resolution
    return cameraMat


def readcalibrationimages(images, checkerboard, targetSquareSize, showCalImages):
    # stop the iteration when specified accuracy, epsilon, is reached or specified number of iterations are completed. 
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 300000, 0.0001) 
    
    # Vector for 3D points 
    threeDPoints = [] 
    # Vector for 2D points 
    twoDPoints = [] 
    
    #  3D points real world coordinates 
    objectp3d = np.zeros((1, checkerboard[0] * checkerboard[1], 3), np.float32) 
    objectp3d[0, :, :2] = targetSquareSize*np.mgrid[0:checkerboard[0], 0:checkerboard[1]].T.reshape(-1, 2) 
    prev_img_shape = None

    # Extracting path of individual image stored in a given directory. 
    imagesAnalyzed = []
    for filename in images: 
        image = cv2.imread(filename) 
        grayColor = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) 
    
        # Find the chess board corners 
        # If desired number of corners are found in the image then ret = true 
        ret, corners = cv2.findChessboardCorners(grayColor, checkerboard) 
    
        # If desired number of corners can be detected then, refine the pixel coordinates and display 
        # them on the images of checker board 
        if ret == True: 
            threeDPoints.append(objectp3d) 
    
            # Refining pixel coordinates for given 2d points. 
            corners2 = cv2.cornerSubPix(grayColor, corners, (15,15), (-1, -1), criteria) 
            twoDPoints.append(corners2)

            # Draw and display the corners 
            image = cv2.drawChessboardCorners(image, checkerboard, corners2, ret)

            # keep track of all the images we analyzed for the calibration (some may fail)
            imName = filename.split("\\")
            imagesAnalyzed.append(imName[-1]) 
        else: 
            imName = filename.split("\\")
            print("image failed in cal: " + imName[-1])
        
        if showCalImages:
            cv2.imshow('img', image) 
            cv2.waitKey(0) 

    cv2.destroyAllWindows() 
    #h, w = image.shape[:2] 
    
    return twoDPoints, threeDPoints, imagesAnalyzed, grayColor.shape[::-1]


def cameracalibration(matrixIn, resolution, twoDPoints, threeDPoints, useFisheyeCalibration):
    # Perform camera calibration from the 3d checkerboard points
    # and corresponding pixel coordinates of the detected corners (twodpoints) 

    if useFisheyeCalibration:
        # the fisheye calibration method from openCV
        # fewer options, but required for accurate wide FOV camera calibration
        ret, cameraMatrix, distortion, r_vecs, t_vecs = cv2.fisheye.calibrate( 
            threeDPoints, twoDPoints, resolution, matrixIn, None, 
            flags=(cv2.fisheye.CALIB_FIX_SKEW + # removes skew factor as an optimization variable (use our initial-guess camera matrix value)
                cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC + # recompute extrinsics on each optimization pass (important for wide-fov camera, probably always good to do)
                cv2.fisheye.CALIB_FIX_PRINCIPAL_POINT + # removes image center point as optimization variable (use our initial-guess camera matrix value); OPTDistortionV1 requires rotational symmetry
                cv2.fisheye.CALIB_CHECK_COND)) 

    else:
        # the basic camera calibration from openCV
        # this is sufficient if the max half-FOV of the camera is less than 50~60deg
        # this method has some additional options, so it is preferred to use when possible
        ret, cameraMatrix, distortion, r_vecs, t_vecs = cv2.calibrateCamera( 
            threeDPoints, twoDPoints, resolution, matrixIn, None, 
            flags=(cv2.CALIB_USE_INTRINSIC_GUESS + # initial matrix guess
                cv2.CALIB_FIX_PRINCIPAL_POINT + # don't allow cx/cy as variable
                cv2.CALIB_RATIONAL_MODEL + # use 6 k-terms
                cv2.CALIB_ZERO_TANGENT_DIST)) # only symmetrical distortion

    return ret, cameraMatrix, distortion, r_vecs, t_vecs


def convertcamerapose(r_vec):
    rotMatrix,_ = cv2.Rodrigues(r_vec.flatten())
    R =  Rotation.from_matrix(rotMatrix)
    # Note: Speos performs intrinsic rotations, so use scipy intrinsic rotation "zyx"
    eulerAngles = R.as_euler("zyx",degrees=True) # zyx rotation also called yaw->pitch->roll
    return eulerAngles


def savecameraextrinsics(imagesAnalyzed, cameraMatrix, distortion, t_vecs, r_vecs, outFn):
    # save the camera intrinsics and the camera pose for each calibration image
    # note about validation:
    # this pose data, converted to euler angles, lets you validate the calibration via speos
    # In speos, you can build a checkerboard model (make sure to match the phsyical checkerboard size), an import the OPTDistortion model generated here.
    # By positioning the camera in precisely the same pose as a given calibratoin image, you should be able to reproduce the checkerboard corner coordinates in the image.
    # OpenCV uses the upper-left checkerboard corner as the reference origin. 
    # So in Speos, starting from that origin, you can apply the rotation (z->y-x) and then the translations, to reproduce the camera pose
    # caution: openCV uses left-handed coordinates, so you'll need to invert the sign of the x rotation and x translation

    txtfile = open(outFn, 'w')

    txtfile.write("\n Camera Intrinsics Matrix:\n")
    txtfile.write(repr(cameraMatrix))
    txtfile.write("\n\n Distortion Params:\n")
    txtfile.write(repr(distortion))
    txtfile.write("\n\n")

    i = 0
    for filename in imagesAnalyzed:
        # convert camera rotation vector into euler angles, for usage in speos
        eulerAngles = convertcamerapose(r_vecs[i])

        imName = filename.split("\\")
        txtfile.write("Calibration Image: " + imName[-1] + "\n")
        txtfile.write("Translation Vector: " + repr(t_vecs[i].flatten()) + "\n") 
        txtfile.write("Rotation Vector: " + repr(r_vecs[i].flatten()) + "\n")
        txtfile.write("Euler Rotation (deg): " + repr(eulerAngles) + "\n")
        txtfile.write("\n")
        i = i+1

    txtfile.close()


def convertdistortiontoangles(cameraMatrix, resolution, distortion, useFisheyeCalibration):
    ## distortion calculation method using projection (sample the object space, and project to distorted image plane)
    ## note: we have to guess (and overshoot) the object angle which will fill the sensor
    # .OPTDistortionV1 requires symmetry, so we assume rotational symmetry, so functionally x=y=r

    # sample >2000 points across image plane
    nSamp = 5001

    # these represent sensor-side (distorted image plane)
    # image plane is at z=efl (from camera matrix)
    efl = 0.5*(cameraMatrix[0,0] + cameraMatrix[1,1]) # EFL (from calibration) in units of pix
    
    # create a set of evenly sampled object points in 3d space
    # overfill the sensor (beyond rMax, the sensor corner) 
    thetaObjMax = 89 #deg
    z = 1 # sample our 3d points at z=1 plane (in front of camera)
    xyzObj = np.zeros((nSamp,1, 3), dtype=np.float32) #note: theres a bug (?) in cv2.fisheye.projectPoints, where it needs an extra dimension in the input array
    for i in range(0, nSamp):
        # maintain y=0, so that r=x and we can work in 1D
        thisTheta = thetaObjMax*(i/(nSamp-1))
        xyzObj[i,0,0] = z*np.tan((np.pi/180)*thisTheta) # sampled object points
        xyzObj[i,0,2] = z

    if useFisheyeCalibration:
        # project the object points using our camera matrix and distortion params
        xyImage, _ = cv2.fisheye.projectPoints(xyzObj, np.zeros((3,1)), np.zeros((3,1)), cameraMatrix, distortion)
    else:
        # if used 'regular' calibration model, then use this function for undistort
        xyImage, _ = cv2.projectPoints(xyzObj, np.zeros((3,1)), np.zeros((3,1)), cameraMatrix, distortion)

    # rebase the image coordinates to the sensor center
    for i in range(0, nSamp):
        xyImage[i,0,0] = xyImage[i,0,0] - 0.5*resolution[0]
        xyImage[i,0,1] = xyImage[i,0,1] - 0.5*resolution[1]
        
        # calibration is a polynomial fit; near the image corner, it could become invalid
        # in that case, just clip the remaining data, since it is unusable
        if xyImage[i,0,0] < xyImage[i-1,0,0]:
            if i==0:
                continue
            xyImage = xyImage[0:i-1, :, :]
            xyzObj = xyzObj[0:i-1,:,:]
            nSamp = (i-1)
            break
    
    '''# compute the raw distortion values as % distortion   
    # this is just for checking distortion, i.e. comparing with Zemax data in a validation case
    import matplotlib.pyplot as plt
    rImage = xyImage[:,0,0]
    rUndistorted = efl*xyzObj[:,0,0] # taking z=efl on object side
    dist = 100*(rImage - rUndistorted) / rUndistorted
    objAngle = (180/np.pi)*np.arctan(rUndistorted/cameraMatrix[0,0])
    plt.scatter(dist, objAngle)'''

    return xyzObj, xyImage,nSamp


def generateoptdistortionfile(xyzObj, xyImage, cameraMatrix, pixelSize, nSamp, optDistortionFn):
    # Write out the .OPTDistortion file
    
    # convert coordinates to angles
    efl = 0.5*(cameraMatrix[0,0] + cameraMatrix[1,1]) # EFL (from calibration) in units of pix
    thetaObj = np.arctan(xyzObj[:,0,0])
    thetaImage = np.arctan(xyImage[:,0,0] / efl)

    with open(optDistortionFn, 'w') as f:
        f.write('OPTIS - Optical distortion file v1.0\n')
        f.write('Created by ZD using opencv distortion data; cal efl = ' + str(efl*pixelSize) + '\n')
        f.write('0\n')
        f.write(str(nSamp))

        f.write('\n' + str(0.0) + ' ' + str(0.0))
        for i in range(1,nSamp):
            f.write('\n' + str(thetaObj[i]) + ' ' + str(thetaImage[i]))

def main():

    # glob the images
    images = glob.glob(imageDir + '*.' + ext) 
    # find the checkerboard coordinates in each cal image
    twoDPoints, threeDPoints, imagesAnalyzed, resolution = readcalibrationimages(images, checkerboard, targetSquareSize, showCalImages)

    # set up an initial guess for the camera intrinsics matrix
    initialCameraMat = buildinitialcameramatrix(efl, resolution[0], resolution[1])

    # run the calibration to find the real camera intrinsics matrix, and camera pose for each cal image
    ret, cameraMatrix, distortion, r_vecs, t_vecs = cameracalibration(initialCameraMat, resolution, twoDPoints, threeDPoints, useFisheyeCalibration)

    # save out the intrinsics and extrinsics
    savecameraextrinsics(imagesAnalyzed, cameraMatrix, distortion, t_vecs, r_vecs, extrinsicsFn)

    # convert distortion data to obj/im angle pairs (the format Speos is expecting)
    xyzObj, xyImage, nSamp = convertdistortiontoangles(cameraMatrix, resolution, distortion, useFisheyeCalibration)

    # save the optdistortion data file
    generateoptdistortionfile(xyzObj, xyImage, cameraMatrix, pixelSize, nSamp, optDistortionFn)


main()




