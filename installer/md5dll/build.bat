@echo Building MD5dll
@set md5unicode=
@if not "%1"=="/u" goto skipU
@set md5unicode=/DNSIS_UNICODE
@:skipU
@REM compile dll
rc /l 0x409 /d "NDEBUG" %md5unicode% md5dll.rc
cl /O2 /GX- /Gs- /Oi /Os /GF /GB /DENABLE_GETMD5FILE /DENABLE_GETMD5STRING /DENABLE_GETMD5RANDOM %md5unicode% md5dll.def md5dll.res md5dll.cpp MD5.cpp kernel32.lib user32.lib /LD /link -opt:nowin98 -opt:REF,ICF -machine:I386 -nodefaultlib -entry:"_DllMainCRTStartup"
::@REM build optional link lib
::lib /DEF:md5dll.def /machine:I386
@REM removing unneeded files
del *.obj
del md5dll.res
del md5dll.exp
del md5dll.lib
@set md5unicode=
@PAUSE
