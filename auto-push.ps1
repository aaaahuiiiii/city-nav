while ($true) {
  # 仅当仓库是 git 仓库时继续
  git rev-parse --is-inside-work-tree 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) {
    Write-Host "Not a git repo here. Ctrl+C to exit."
    Start-Sleep -Seconds 5
    continue
  }

  # 暂存变化（交给 .gitignore 过滤）
  git add -A | Out-Null

  # 只有有暂存变化时才提交
  git diff --cached --quiet
  if ($LASTEXITCODE -ne 0) {
    $msg = "auto: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    git commit -m $msg | Out-Null

    # 尝试与远端对齐，减少冲突
    git pull --rebase origin main | Out-Null

    # 推送
    git push origin main | Out-Null
    Write-Host "Pushed at $msg"
  }

  Start-Sleep -Seconds 30   # 每 30 秒检查一次
}
