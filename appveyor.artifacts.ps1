$version = Get-Content version.txt
$filename = "PIME-$version-setup.exe"
Push-AppveyorArtifact "installer\$filename" -FileName $filename
