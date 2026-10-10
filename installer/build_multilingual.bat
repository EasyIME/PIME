@echo off
setlocal
cd /d "%~dp0"

set "BASE_DIR=PIME_Core\bin\x86\Release"
set "MSI_EN=%BASE_DIR%\en-US\PIME_Core.msi"
set "MSI_TW=%BASE_DIR%\zh-TW\PIME_Core.msi"
set "MSI_CN=%BASE_DIR%\zh-CN\PIME_Core.msi"
set "MSI_OUT=PIME_Core_Multilingual.msi"

set "WSCRIPT_DIR=C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64"

echo Generating transforms...
wix msi transform "%MSI_EN%" "%MSI_TW%" -out zh-TW.mst
wix msi transform "%MSI_EN%" "%MSI_CN%" -out zh-CN.mst

echo Copying base MSI...
copy /y "%MSI_EN%" "%MSI_OUT%"

echo Embedding transforms...
cscript //nologo "%WSCRIPT_DIR%\wisubstg.vbs" "%MSI_OUT%" zh-TW.mst 1028
cscript //nologo "%WSCRIPT_DIR%\wisubstg.vbs" "%MSI_OUT%" zh-CN.mst 2052

echo Updating Summary Information languages...
cscript //nologo "%WSCRIPT_DIR%\wilangid.vbs" "%MSI_OUT%" Package 1033,1028,2052

echo Cleaning up intermediate files...
del zh-TW.mst
del zh-CN.mst

echo Done! Output is %MSI_OUT%
endlocal
