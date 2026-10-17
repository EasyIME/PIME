$version = (Get-Content version.txt).Trim()
$filename = "PIME-$version.msi"
$sourcePath = "installer\bin\PIME_Core_Multilingual.msi"
if (-not (Test-Path $sourcePath)) {
    $sourcePath = "installer\PIME_Core_Multilingual.msi"
}
if (Test-Path $sourcePath) {
    Copy-Item $sourcePath "installer\$filename"
    Push-AppveyorArtifact "installer\$filename" -FileName $filename
}
