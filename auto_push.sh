# auto-push.ps1  — 每 30 秒自动提交一次有变化的内容并推送
while ($true) {
  # 过滤掉 .git、本地依赖与临时文件（请确保 .gitignore 已正确配置）
  git add -A

  # 仅当有暂存变化时才提交
  $hasStaged = git diff --cached --quiet; $exit = $LASTEXITCODE
  if ($exit -ne 0) {
    $msg = "auto: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    git commit -m $msg | Out-Null
    # 与远端对齐，尽量避免冲突
    git pull --rebase origin main | Out-Null
    git push origin main | Out-Null
    Write-Host "Pushed at $msg"
  }

  Start-Sleep -Seconds 30
}
