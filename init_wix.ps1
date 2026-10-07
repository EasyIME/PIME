# init_wix.ps1
$ErrorActionPreference = "Stop"

# Create root wix directory
New-Item -ItemType Directory -Force -Path "wix" | Out-Null

$projects = @(
    @{ Name="PIME_Core"; Type="package"; Arch="x86" },
    @{ Name="PIME_TextService_x86"; Type="package"; Arch="x86" },
    @{ Name="PIME_TextService_x64"; Type="package"; Arch="x64" },
    @{ Name="PIME_TextService_arm64"; Type="package"; Arch="arm64" },
    @{ Name="PIME_Setup"; Type="bundle"; Arch="x86" }
)

foreach ($proj in $projects) {
    $dir = "wix\$($proj.Name)"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    
    # Create wixproj
    $projContent = @"
<Project Sdk="WixToolset.Sdk/4.0.0">
  <PropertyGroup>
    <Platforms>x86;x64;ARM64</Platforms>
    <Platform>$($proj.Arch)</Platform>
  </PropertyGroup>
</Project>
"@
    Set-Content -Path "$dir\$($proj.Name).wixproj" -Value $projContent -Encoding UTF8

    if ($proj.Type -eq "package") {
        $wxsContent = @"
<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">
  <Package Name="$($proj.Name)" Manufacturer="EasyIME" Version="1.0.0.0" UpgradeCode="PUT-GUID-HERE">
    <StandardDirectory Id="ProgramFilesFolder">
      <Directory Id="INSTALLFOLDER" Name="PIME" />
    </StandardDirectory>
    <Feature Id="Main">
      <ComponentGroupRef Id="ExampleComponents" />
    </Feature>
  </Package>
  <Fragment>
    <ComponentGroup Id="ExampleComponents" Directory="INSTALLFOLDER">
      <Component>
        <File Source="..\..\version.txt" />
      </Component>
    </ComponentGroup>
  </Fragment>
</Wix>
"@
        Set-Content -Path "$dir\Package.wxs" -Value $wxsContent -Encoding UTF8
    } else {
        $wxsContent = @"
<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs" xmlns:bal="http://wixtoolset.org/schemas/v4/wxs/bal">
  <Bundle Name="PIME" Manufacturer="EasyIME" Version="1.0.0.0" UpgradeCode="PUT-GUID-HERE">
    <BootstrapperApplication>
      <bal:WixStandardBootstrapperApplication LicenseUrl="" Theme="hyperlinkLicense" />
    </BootstrapperApplication>
    <Chain>
      <MsiPackage SourceFile="..\PIME_Core\bin\x86\Debug\en-US\PIME_Core.msi" />
      <!-- Add architecture conditions for the others -->
    </Chain>
  </Bundle>
</Wix>
"@
        Set-Content -Path "$dir\Bundle.wxs" -Value $wxsContent -Encoding UTF8
    }
}

# Create solution
dotnet new sln -n PIME_WiX -o wix
foreach ($proj in $projects) {
    dotnet sln wix/PIME_WiX.sln add wix/$($proj.Name)/$($proj.Name).wixproj
}
