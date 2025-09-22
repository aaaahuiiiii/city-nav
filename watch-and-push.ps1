$path = (Get-Location).Path
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $path
$watcher.IncludeSubdirectories = $true
$watcher.Filter = "*.*"
$watcher.EnableRaisingEvents = $true

$timer = New-Object Timers.Timer
$timer.Interval = 2000  # 2s 去抖
$timer.AutoReset = $false

$action = {
  git add -A | Out-Null
  git diff --cached --quiet
  if ($LASTEXITCODE -ne 0) {
    $msg = "auto: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    git commit -m $msg | Out-Null
    git pull --rebase origin main | Out-Null
    git push origin main | Out-Null
    Write-Host "Pushed at $msg"
  }
}

Register-ObjectEvent -InputObject $watcher -EventName Changed -Action { $timer.Stop(); $timer.Start() } | Out-Null
Register-ObjectEvent -InputObject $watcher -EventName Created -Action { $timer.Stop(); $timer.Start() } | Out-Null
Register-ObjectEvent -InputObject $watcher -EventName Deleted -Action { $timer.Stop(); $timer.Start() } | Out-Null
Register-ObjectEvent -InputObject $timer   -EventName Elapsed -Action $action | Out-Null

Write-Host "Watching $path ... Ctrl+C to stop."
while ($true) { Start-Sleep -Seconds 1 }
