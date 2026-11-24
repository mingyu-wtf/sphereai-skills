# Makes a folder link named "uploads" inside every Aside session folder, pointing at your work folder.
# Aside can only read local files through "<session folder>\uploads\...". Without this link, file
# uploads arrive as empty (0 byte) files and the editor shows "upload failed".
#
# Usage (PowerShell, Windows):
#   powershell -NoProfile -File make_uploads_junction.ps1 -Work "C:\blog_work"            # one pass
#   powershell -NoProfile -File make_uploads_junction.ps1 -Work "C:\blog_work" -Watch     # keep running
#
# -Profile is the number in the Aside profile folder name (...\.aside\u\<Profile>\sessions). Default 0.
# Aside creates a NEW session folder each time it starts, so run with -Watch in a separate window
# before you start Aside work, and leave it open. Close it with Ctrl+C when you are done.
param(
  [Parameter(Mandatory = $true)][string]$Work,
  [string]$Profile = "0",
  [switch]$Watch,
  [switch]$All
)

if (-not (Test-Path $Work)) { New-Item -ItemType Directory -Path $Work | Out-Null }
$Work = (Resolve-Path $Work).Path
$Sessions = Join-Path $env:USERPROFILE ".aside\u\$Profile\sessions"
if (-not (Test-Path $Sessions)) {
  Write-Host "Sessions folder not found: $Sessions"
  Write-Host "Start Aside once, or check the profile number (folders under $env:USERPROFILE\.aside\u)."
  exit 1
}

# Only the newest sessions are checked (old ones may number in the thousands and make a pass take minutes).
# Add -All to link every session folder.
$warned = @{}
function Link-All {
  $dirs = Get-ChildItem $Sessions -Directory | Sort-Object LastWriteTime -Descending
  if (-not $All) { $dirs = $dirs | Select-Object -First 30 }
  $dirs | ForEach-Object {
    $j = Join-Path $_.FullName "uploads"
    if (-not (Test-Path $j)) {
      New-Item -ItemType Junction -Path $j -Target $Work | Out-Null
      Write-Host "linked: $j -> $Work"
    } elseif (-not $warned.ContainsKey($j)) {
      $warned[$j] = $true
      $t = (Get-Item $j).Target
      if ($t -and ($t -ne $Work)) { Write-Host "note: $j already points to $t (left as is)" }
    }
  }
}

do {
  Link-All
  if ($Watch) { Start-Sleep -Seconds 3 }
} while ($Watch)
