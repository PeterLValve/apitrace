@ECHO off

REM Clean up after old builds
IF EXIST "build32%CONFIG%log.txt" del "build32%CONFIG%log.txt"
IF EXIST "build64%CONFIG%log.txt" del "build64%CONFIG%log.txt"

REM default to the Release configuration
IF NOT "%3"=="" (
   set CONFIG=%3
) ELSE (
   set CONFIG=Release
)

IF "%1"=="cmake32" GOTO cmake32
IF "%1"=="build32" GOTO build32
IF "%1"=="copy32" GOTO copy32
IF "%1"=="skip32" GOTO skip32

REM call "%VS100COMNTOOLS%vcvarsall.bat"

REM
REM Regenerate win32 solution and build the config 
REM

:cmake32
ECHO Regenerating 32-bit solution file using Cmake
IF EXIST .\win32 rmdir /S /Q .\win32
cmake -H%cd% -B%cd%\win32\ -G "Visual Studio 10"

:build32
ECHO Compiling 32-bit %CONFIG% binaries
"%VS100COMNTOOLS%..\IDE\devenv.exe" .\win32\apitrace.sln /Build "%CONFIG%" /Out "build32%CONFIG%log.txt"

:copy32
p4 edit "win32\%CONFIG%\..."
p4 revert "win32\%CONFIG%\Qt*.dll"
ECHO Removing old 32-bit %CONFIG% wrappers
IF EXIST ".\win32\%CONFIG%\wrappers" rmdir /S /Q ".\win32\%CONFIG%\wrappers"

ECHO Copying newly built 32-bit %CONFIG% wrappers
IF NOT EXIST "win32\%CONFIG%\wrappers" mkdir "win32\%CONFIG%\wrappers"
xcopy "win32\wrappers\%CONFIG%\*.dll" "win32\%CONFIG%\wrappers\"
xcopy "win32\wrappers\%CONFIG%\*.pdb" "win32\%CONFIG%\wrappers\"

:skip32

IF "%2"=="cmake64" GOTO cmake64
IF "%2"=="build64" GOTO build64
IF "%2"=="copy64" GOTO copy64
if "%2"=="skip64" GOTO skip64

@ECHO OFF

REM
REM Regenerate win64 solution and build the config
REM

:cmake64
ECHO Regenerating 64-bit solution file using Cmake
IF EXIST .\win64 rmdir /S /Q .\win64
cmake -DENABLE_GUI=FALSE -H%cd% -B%cd%\win64\ -G "Visual Studio 10 Win64"

:build64
ECHO Compiling 64-bit %CONFIG% binaries
"%VS100COMNTOOLS%..\IDE\devenv.exe" .\win64\apitrace.sln /Build %CONFIG% /Out build64%CONFIG%log.txt

:copy64
p4 edit "win64\%CONFIG%\..."
ECHO Removing old 64-bit %CONFIG% wrappers
IF EXIST ".\win64\%CONFIG%\wrappers" rmdir /S /Q ".\win64\%CONFIG%\wrappers"

ECHO Copying newly built 64-bit %CONFIG% wrappers
IF NOT EXIST "win64\%CONFIG%\wrappers"  mkdir "win64\%CONFIG%\wrappers\"
xcopy "win64\wrappers\%CONFIG%\*.dll" "win64\%CONFIG%\wrappers\"
xcopy "win64\wrappers\%CONFIG%\*.pdb" "win64\%CONFIG%\wrappers\"

:skip64