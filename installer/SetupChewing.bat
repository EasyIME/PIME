mkdir %USERPROFILE%\ChewingTextService
attrib +h %USERPROFILE%\ChewingTextService
cacls "%USERPROFILE%\ChewingTextService" /e /t /g "ALL APPLICATION PACKAGES:c"
