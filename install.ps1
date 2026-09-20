# ====================================================================================
# PROJECT SAVER AUTOMATED NETWORK INSTALLATION & VALIDATION ENGINE
# irm https://gowildchild.github.io/Project-Saver/install.ps1 | iex
# ====================================================================================
$InstallVersion = "v0.0.73"
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
    Write-Host "`n[🚨] SECURITY BARRICADE: SHA-256 Integrity Hash Mismatch!" -ForegroundColor Red
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
    "endpoint"          = "http://localhost:19763"
    "serverToken"       = $NewToken
    "bodyFilenameField" = "file"
    "bodyUrlField"      = "url"
    "destination"       = "server"
    "autoSave"          = "none"
} | ConvertTo-Json

$JsonPath = Join-Path $InstallDir "singlefile-project-saver-config.json"
Set-Content -Path $JsonPath -Value $SingleFileConfig -Encoding UTF8

$CfgPath = Join-Path $InstallDir "project_saver.cfg"
$CfgContent = @(
    "token=$NewToken"
    "export_folder=$ExportFolder"
)
$CfgContent | Set-Content -Path $CfgPath

# 8. Generate Desktop Shortcut natively via Windows Shell API objects
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $BinPath
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.Description = "Project Saver Daemon"
$Shortcut.IconLocation = "shell32.dll,44"
$Shortcut.Save()

$BoxTotalWidth = 60
$VersionText   = "  │ Version Deployed : $LatestVersion"
$PaddingNeeded = $BoxTotalWidth - $VersionText.Length - 1

if ($PaddingNeeded -lt 0) { $PaddingNeeded = 0 }
$PadSpaces     = " " * $PaddingNeeded

# Force the output encoding to handle the shapes locally
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n  ┌────────────────────────────────────────────────────────────┐" -ForegroundColor Green
Write-Host "  │   SUCCESS: Project Saver Installation Complete!            │" -ForegroundColor Green
Write-Host "  ├────────────────────────────────────────────────────────────┤" -ForegroundColor Green
Write-Host "$VersionText$PadSpaces  │" -ForegroundColor Green
Write-Host "  │ Security Check   : SHA-256 Verified (Match Confirmed)      │" -ForegroundColor Green
Write-Host "  │ Location Locked  : AppData\Local\ProjectSaver              │" -ForegroundColor Green
Write-Host "  │ Created By       : Gunther Voet                            │" -ForegroundColor Green
Write-Host "  └────────────────────────────────────────────────────────────┘`n" -ForegroundColor Green

# ====================================================================================
# 9. AUTOMATED WINDOWS TASK SCHEDULER INTERACTIVE STARTUP REGISTRATION
# ====================================================================================
Write-Host "[*] Registering automated interactive logon startup triggers..." -ForegroundColor Cyan

$TaskName = "ProjectSaverDaemon"
$TaskDescription = "Launches Project Saver interactive updater countdown and background port service daemon on user logon."

# Verify if an old instance configuration task is already tracked inside system tables, and clear it out gracefully
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "[*] Removing legacy task scheduling definitions..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
}

try {
    # 1. Define the execution boundary parameters to run natively when your specific user logs in
    $Trigger = New-ScheduledTaskTrigger -AtLogOn

    # 2. Configure the action loop to boot your application executable directly inside a visible console wrapper frame
    # Crucial trick: We point arguments directly to powershell executing your path to prevent invisible background process hang blocks
    $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Normal -Command & '$BinPath'"

    # 3. Establish structural policy controls to allow processing on laptops/battery power scopes cleanly
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -Compatibility Win8

    # 4. Inject the interactive configuration variables natively straight into the local Task Scheduler database engine
    Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger -Action $Action -Settings $Settings -Description $TaskDescription | Out-Null
    
    Write-Host "[+] Interactive startup automation tasks registered successfully!" -ForegroundColor Green
    Write-Host "    -> Project Saver will now boot visibly inside a prompt window on your next Windows Logon." -ForegroundColor Gray
} catch {
    Write-Host "[-] Automation Error: Could not provision scheduled task triggers. Run installer as Admin if required." -ForegroundColor Red
}

Write-Host "📂 QUICK NAVIGATION LINKS" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------"
Write-Host " -> Press [A] to instantly open the Application Core Folder" -ForegroundColor Yellow
Write-Host " -> Press [E] to instantly open the Export Files Folder" -ForegroundColor Yellow
Write-Host " -> Press [Enter] to exit this installer setup wizard safely" -ForegroundColor Gray
Write-Host "------------------------------------------------------------"

$MyDocuments = [Environment]::GetFolderPath('MyDocuments')
$ExportFolder = Join-Path $MyDocuments "Project-Saver\export"

while ($true) {
    Write-Host -NoNewline "`r[?] Select navigation destination index action: "
    $KeyInfo = [Console]::ReadKey($true)
    $KeyChar = $KeyInfo.KeyChar.ToString().ToLower()

    if ($KeyChar -eq 'a') {
        Write-Host "Opening Application folder...                      " -ForegroundColor Green
        Start-Process explorer.exe -ArgumentList "`"$InstallDir`""
    }
    elseif ($KeyChar -eq 'e') {
        # Safely create the export directory profile if it doesn't exist yet so explorer doesn't throw a crash error
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
