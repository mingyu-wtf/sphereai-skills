# 스레드 자동 운영 러너 (Windows 작업 스케줄러가 10분마다 실행)
# 1) due.py 로 지금 할 일을 묻고, 없으면 바로 끝낸다(Claude를 부르지 않음 = 토큰 0)
# 2) 할 일이 있으면 prompt.md + "지금 할 일"을 claude -p 에 넘긴다
# 3) 겹쳐 실행되지 않게 잠금 파일을 쓴다
# 이 파일은 작업 폴더의 scripts\ 안에 둔다. 작업 폴더 = 이 파일의 상위 폴더(config.json이 있는 곳).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = New-Object System.Text.UTF8Encoding $false

$cfg = Get-Content -LiteralPath (Join-Path $root "config.json") -Raw -Encoding utf8 | ConvertFrom-Json
$logDir = Join-Path $root $cfg.paths.run_log_dir
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir ("run_" + (Get-Date -Format "yyyyMMdd") + ".log")
$lock = Join-Path $root "run.lock"

if (Test-Path -LiteralPath $lock) {
    $age = (Get-Date) - (Get-Item -LiteralPath $lock).LastWriteTime
    if ($age.TotalMinutes -lt 60) { exit 0 }   # 이전 실행이 아직 도는 중
}

$due = (& python scripts\due.py) -join ""
if (-not $due -or $due -eq "[]") { exit 0 }

Set-Content -LiteralPath $lock -Value (Get-Date -Format "yyyy-MM-dd HH:mm") -Encoding utf8
try {
    Add-Content -LiteralPath $log -Value ("`n==== " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " due: " + $due) -Encoding utf8
    $promptFile = Join-Path $root $cfg.paths.prompt
    $prompt = (Get-Content -LiteralPath $promptFile -Raw -Encoding utf8) + "`n`n## 지금 할 일`n" + $due
    $tools = @($cfg.claude_allowed_tools)
    $out = $prompt | & claude -p --permission-mode acceptEdits --allowedTools $tools 2>&1
    Add-Content -LiteralPath $log -Value ($out -join "`n") -Encoding utf8
}
finally {
    Remove-Item -LiteralPath $lock -Force -ErrorAction SilentlyContinue
}
