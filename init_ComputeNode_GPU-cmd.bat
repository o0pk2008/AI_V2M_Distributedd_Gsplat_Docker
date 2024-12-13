@echo off
REM Set encoding to UTF-8
@chcp 65001 >nul

REM Define variables
set HOST_PATH=E:\Python\AI_V2M_Distributedd_Gsplat_Docker
set CONTAINER_PATH=/source/object_server
set IMAGE_NAME=nerfstudio:v6
set CONTAINER_NAME=nerfstudio_container

REM Check if host path exists
if not exist "%HOST_PATH%" (
    echo Error: Host path %HOST_PATH% does not exist.
    exit /b
)

REM Stop and remove any existing container with the same name
docker stop %CONTAINER_NAME% 2>nul
docker rm %CONTAINER_NAME% 2>nul

REM Start Docker container, mount host path, and keep it running interactively with bash
docker run --rm -it --gpus all ^
  --name %CONTAINER_NAME% ^
  -v %HOST_PATH%:%CONTAINER_PATH% ^
  -p 5201:5201 ^
  %IMAGE_NAME% ^
  /bin/bash -c "source /root/miniconda3/etc/profile.d/conda.sh && conda activate nerfstudio && exec /bin/bash"

REM Check exit code of the last command
if %errorlevel% neq 0 (
    echo Error: Failed to run Docker container.
    exit /b
)

echo Docker container ran successfully.
