# ====================================================================================
# PROJECT SAVER AUTOMATED NETWORK INSTALLATION & VALIDATION ENGINE
# irm https://gowildchild.github.io/Project-Saver/install.ps1 | iex
# ====================================================================================
$InstallVersion = "v0.0.80"
$ErrorActionPreference = "Stop"
$RepoOwner = "gowildchild"
$RepoName  = "Project-Saver"

$InstallDir = Join-Path $env:USERPROFILE "AppData\Local\ProjectSaver"
$MyDocuments = [Environment]::GetFolderPath('MyDocuments')
$ExportFolder = Join-Path $MyDocuments "Project-Saver\export"
$BinPath = Join-Path $InstallDir "project_saver.exe"
$ManifestPath = Join-Path $InstallDir "manifest.txt"
$ShortcutPath = "$([Environment]::GetFolderPath('Desktop'))\Project Saver.lnk"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Project Saver Verified Network Setup ($InstallVersion)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Fetch live production release definitions from GitHub API
Write-Host "[*] Querying latest active release definitions from GitHub API"
$ApiUrl = "https://api.github.com/repos/$RepoOwner/$RepoName/releases/latest"
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $ReleaseData = Invoke-RestMethod -Uri $ApiUrl -Method Get -Headers @{"User-Agent"="Project-Saver-Installer"}
} catch {
    Write-Host "[-] Network Transaction Error: Could not connect to GitHub API." -ForegroundColor Red
    return
}

$LatestVersion = $ReleaseData.tag_name
Write-Host "[+] Target release version isolated: [$LatestVersion]" -ForegroundColor Green

# 2. Extract specific binary asset URLs
$ExeAsset = $ReleaseData.assets | Where-Object { $_.name -like "*.exe" -and $_.name -notlike "*setup*" } | Select-Object -First 1
$ManifestAsset = $ReleaseData.assets | Where-Object { $_.name -eq "manifest.txt" } | Select-Object -First 1

if (-not $ExeAsset -or -not $ManifestAsset) {
    Write-Host "[-] Critical Error: Missing executable or manifest file in release." -ForegroundColor Red
    return
}

$TempFolder = Join-Path ([System.IO.Path]::GetTempPath()) "ProjectSaver_Setup"
if (Test-Path $TempFolder) { Remove-Item $TempFolder -Recurse -Force | Out-Null }
New-Item -ItemType Directory -Path $TempFolder | Out-Null

$TempExePath = Join-Path $TempFolder $ExeAsset.name
$TempManifestPath = Join-Path $TempFolder "manifest.txt"

# 4. Download files down into temporary sandbox
Write-Host "[*] Fetching delivery assets for integrity verification..."
Invoke-WebRequest -Uri $ExeAsset.browser_download_url -OutFile $TempExePath -UseBasicParsing
Invoke-WebRequest -Uri $ManifestAsset.browser_download_url -OutFile $TempManifestPath -UseBasicParsing

# 5. DYNAMIC CRYPTOGRAPHIC SHA-256 VALIDATION 
Write-Host "[*] Evaluating security footprint hash keys..."

$ManifestContent = Get-Content -Path $TempManifestPath
$OfficialHashLine = $ManifestContent | Where-Object { $_.Contains("SHA-256 Checksum") } | Select-Object -First 1

if (-not $OfficialHashLine) {
    Write-Host "[-] Verification Error: Manifest format is malformed or invalid." -ForegroundColor Red
    return
}

$OfficialHash = ($OfficialHashLine.Split(":")[1]).Trim().ToLower()
$LocalHash = (Get-FileHash -Path $TempExePath -Algorithm SHA256).Hash.ToLower()

Write-Host "    -> Expected Hash: $OfficialHash" -ForegroundColor Yellow
Write-Host "    -> Computed Hash: $LocalHash" -ForegroundColor Yellow

if ($LocalHash -ne $OfficialHash) {
    Write-Host "`n[!] SECURITY BARRICADE: SHA-256 Integrity Hash Mismatch!" -ForegroundColor Red
    Write-Host "    The downloaded application executable failed security checksum validation." -ForegroundColor Red
    Write-Host "    Installation aborted automatically to protect machine." -ForegroundColor Red
    Remove-Item $TempFolder -Recurse -Force | Out-Null
    return
}
Write-Host "[+] Cryptographic Verification Passed: Binary file code matches perfectly." -ForegroundColor Green

# 6a Copy verified files to production AppData workspace environment path
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir | Out-Null
}
Copy-Item -Path $TempExePath -Destination $BinPath -Force
Copy-Item -Path $TempManifestPath -Destination $ManifestPath -Force
Remove-Item $TempFolder -Recurse -Force | Out-Null

# 6b Install in path
Write-Host "[*] Registering installation folder path inside system environment..."
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -split ";" -notcontains $InstallDir) {
    $NewUserPath = "$UserPath;$InstallDir"
    [Environment]::SetEnvironmentVariable("Path", $NewUserPath, "User")
    $env:Path = "$env:Path;$InstallDir" 
    Write-Host "[+] Environmental paths updated successfully." -ForegroundColor Green
} else {
    Write-Host "[+] Installation path is already registered inside environment scopes." -ForegroundColor Gray
}

# 7. Provision SingleFile configuration files automatically with secure port 19763
Write-Host "[*] Provisioning unique browser extension connection tokens..."
$NewToken = [Guid]::NewGuid().ToString("N")
$SingleFileConfig = @{
    "profiles" = @{
        "Project Saver" = @{
            "saveToRestFormApi"              = $true
            "saveToRestFormApiUrl"           = "http://localhost:19763"
            "saveToRestFormApiToken"         = $NewToken
            "saveToRestFormApiFileFieldName" = "file"
            "saveToRestFormApiUrlFieldName"  = "url"
        }
    }
} | ConvertTo-Json -Depth 4

$JsonPath = Join-Path $InstallDir "singlefile-project-saver-config.json"
$CfgPath = Join-Path $InstallDir "project_saver.cfg"

# STACKOVERFLOW FIX: Native .NET methods force 100% pure, BOM-less UTF-8 writing to disk
[System.IO.File]::WriteAllText($JsonPath, $SingleFileConfig)

$CfgContent = @(
    "token=$NewToken"
    "export_folder=$ExportFolder"
)
[System.IO.File]::WriteAllLines($CfgPath, $CfgContent)

# 8. Generate Desktop Shortcut natively via Windows Shell API objects
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $BinPath
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.Description = "Project Saver Daemon"
$Shortcut.IconLocation = "shell32.dll,44"
$Shortcut.Save()

$TL = [string][char]0x250C  # ┌
$TR = [string][char]0x2510  # ┐
$BL = [string][char]0x2514  # └
$BR = [string][char]0x2518  # ┘
$HZ = [string][char]0x2500  # ─
$VT = [string][char]0x2502  # │
$DV = [string][char]0x251C  # ├
$RV = [string][char]0x2524  # ┤

$LineHZ = $HZ * 60
$TopBar = $TL + $LineHZ + $TR
$Divider = $DV + $LineHZ + $RV
$BottomBar = $BL + $LineHZ + $BR

# Dynamic space padding calculation to keep the right border straight
$BoxTotalWidth = 60
$VersionText = $VT + " Version Deployed : $LatestVersion"
$PaddingNeeded = $BoxTotalWidth - $VersionText.Length - 1

if ($PaddingNeeded -lt 0) { $PaddingNeeded = 0 }
$PadSpaces = " " * $PaddingNeeded

# Force the local console output manager to translate strings using clean UTF-8 tables
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n  $TopBar" -ForegroundColor Green
Write-Host "  $VT   SUCCESS: Project Saver Installation Complete!            $VT" -ForegroundColor Green
Write-Host "  $Divider" -ForegroundColor Green
Write-Host "  $VersionText$PadSpaces  $VT" -ForegroundColor Green
Write-Host "  $VT Security Check   : SHA-256 Verified (Match Confirmed)      $VT" -ForegroundColor Green
Write-Host "  $VT Location Locked  : AppData\Local\ProjectSaver              $VT" -ForegroundColor Green
Write-Host "  $VT Created By       : Gunther Voet                            $VT" -ForegroundColor Green
Write-Host "  $BottomBar`n" -ForegroundColor Green

# 9. AUTOMATED WINDOWS TASK SCHEDULER INTERACTIVE STARTUP REGISTRATION
Write-Host "[*] Registering automated interactive logon startup triggers..." -ForegroundColor Cyan

$TaskName = "ProjectSaverDaemon"
$TaskDescription = "Launches Project Saver interactive updater countdown and background port service daemon on user logon."

$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
}

try {
    $Trigger = New-ScheduledTaskTrigger -AtLogOn
    $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Normal -Command & '$BinPath'"
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -Compatibility Win8

    Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger -Action $Action -Settings $Settings -Description $TaskDescription | Out-Null
    Write-Host "[+] Interactive startup automation tasks registered successfully!" -ForegroundColor Green
} catch {
    Write-Host "[-] Automation Error: Could not provision scheduled task triggers." -ForegroundColor Red
}

# ====================================================================================
# 10. INTERACTIVE POST-INSTALL WORKSPACE NAVIGATION DASHBOARD
# ====================================================================================
Write-Host "`n  QUICK NAVIGATION LINKS" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------"
Write-Host " -> Press [A] to open the Application Core Folder" -ForegroundColor Yellow
Write-Host " -> Press [E] to open the Export Files Folder" -ForegroundColor Yellow
Write-Host " -> Press [Enter] to exit this installer setup wizard safely" -ForegroundColor Gray
Write-Host "------------------------------------------------------------"

# CRITICAL DRAIN FIX: Wipes out the remaining internet script data blocks from terminal memory
while ([Console]::KeyAvailable) { [Console]::ReadKey($true) | Out-Null }

while ($true) {
    Write-Host -NoNewline "`r[?] Select navigation destination: "
    $KeyInfo = [Console]::ReadKey($true)
    $KeyChar = $KeyInfo.KeyChar.ToString().ToLower()

    if ($KeyChar -eq 'a') {
        Write-Host "Opening Application folder...                      " -ForegroundColor Green
        Start-Process explorer.exe -ArgumentList "`"$InstallDir`""
    }
    elseif ($KeyChar -eq 'e') {
        if (-not (Test-Path $ExportFolder)) { 
            New-Item -ItemType Directory -Path $ExportFolder | Out-Null 
        }
        Write-Host "Opening Export folder...                      " -ForegroundColor Green
        Start-Process explorer.exe -ArgumentList "`"$ExportFolder`""
    }
    elseif ($KeyInfo.Key -eq 'Enter') {
        Write-Host "Exiting installer safely. Goodbye!           " -ForegroundColor Gray
        break
    }
}

