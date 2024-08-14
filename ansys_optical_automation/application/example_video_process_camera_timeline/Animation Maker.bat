@echo off

Title Animation Maker

REM ===========================================
REM INPUTS
REM ===========================================

Echo.
Echo ************** SET VARIABLES **************
Echo.
	
set VERSION=242
set SPEOS_INSTALLATION=%AWP_ROOT242%
set SCDM_PYTHON="%AWP_ROOT242%\commonfiles\CPython\3_10\winx64\Release\python\python.exe"

Set LOCAL_FOLDER=%~dp0
Set SCRIPT_FOLDER=%LOCAL_FOLDER%\SCRIPTS

set ANIMATIONMAKER_SCRIPT_PATH="%SCRIPT_FOLDER%\Animation_maker_yml.py"
set VIDEOMAKER_SCRIPT_PATH="%SCRIPT_FOLDER%\Video_maker_yml.py"
set ANIMATION_INPUTS_PATH="%SCRIPT_FOLDER%\Animation_Inputs.yml"


REM ===========================================
REM CHECK PREREQUISITS
REM ===========================================

Echo.
Echo ********** CHECK PREREQUISITS *************
Echo.

"%AWP_ROOT242%\commonfiles\CPython\3_10\winx64\Release\python\python.exe" -m pip install opencv-python

REM pause

REM ===========================================
REM OPEN SCDOCX + RUN SCRIPT 
REM ===========================================

Echo.
Echo *********** RUN SIMULATIONS ***************
Echo.

call "%SPEOS_INSTALLATION%\scdm\SpaceClaim.exe" /AddInManifestFile="%SPEOS_INSTALLATION%\Optical Products\SPEOS\Bin\SpeosSC.Manifest.xml" /RunScript=%ANIMATIONMAKER_SCRIPT_PATH% "%ANIMATION_INPUTS_PATH%" /ScriptArgs="%ANIMATION_INPUTS_PATH%" /ExitAfterScript=True /Splash=False /Headless=False /Splash=False /Welcome=False /ExitAfterScript=True /UseCurrentDirectory=True /ScriptAPI=%VERSION%

pause

REM ===========================================
REM MAKE VIDEO
REM ===========================================

Echo.
Echo ************** MAKE VIDEO *****************
Echo.	
	
"%AWP_ROOT242%\commonfiles\CPython\3_10\winx64\Release\python\python.exe" "%VIDEOMAKER_SCRIPT_PATH%" "%ANIMATION_INPUTS_PATH%"
pause



