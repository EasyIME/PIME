$version = Get-Content version.txt
$filename = "PIME-$version-setup.exe"
$sourcePath = "installer\PIME_Setup\bin\x86\Release\PIME_Setup.exe"
if (Test-Path $sourcePath) {
    Copy-Item $sourcePath "installer\$filename"
    Push-AppveyorArtifact "installer\$filename" -FileName $filename
}
