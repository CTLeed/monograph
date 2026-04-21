# tuesday_research.ps1
#
# Fired by Task Scheduler each Tuesday at 7 AM.
# Reads the top product from backlog.txt and launches `chat.py research`,
# which copies the prompt to the clipboard and opens the chosen chat
# provider. You paste, wait, copy the response, press Enter in this
# terminal, and Ollama takes over after that.

$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'

$root = 'D:\ForFun\monograph'
Set-Location $root

$backlog = Join-Path $root 'backlog.txt'
if (-not (Test-Path $backlog)) {
    Write-Host ''
    Write-Host 'backlog.txt does not exist.' -ForegroundColor Yellow
    Write-Host 'Run `python tools\chat.py pick` to populate it.' -ForegroundColor Yellow
    Write-Host ''
    Read-Host 'Press Enter to close this window'
    exit 1
}

$lines = Get-Content -Path $backlog -Encoding utf8 |
    Where-Object { $_ -and $_.Trim() -and -not $_.Trim().StartsWith('#') }

if (-not $lines) {
    Write-Host ''
    Write-Host 'backlog.txt is empty.' -ForegroundColor Yellow
    Write-Host 'Run `python tools\chat.py pick` to refill it.' -ForegroundColor Yellow
    Write-Host ''
    Read-Host 'Press Enter to close this window'
    exit 1
}

$product = $lines[0].Trim()

Write-Host ''
Write-Host '=================================================='
Write-Host " Monograph — Tuesday morning research"
Write-Host '=================================================='
Write-Host ''
Write-Host " Next product: $product" -ForegroundColor Cyan
Write-Host " Provider:     claude (edit this script to change)"
Write-Host ''
Write-Host ' Steps:'
Write-Host '   1. Prompt is copied to your clipboard.'
Write-Host '   2. Browser opens Claude.ai/new.'
Write-Host '   3. Paste (Ctrl+V), Enter, wait.'
Write-Host '   4. Ctrl+A, Ctrl+C on the response.'
Write-Host '   5. Return here and press Enter.'
Write-Host ''

python tools\chat.py research --product $product --provider claude

$code = $LASTEXITCODE
Write-Host ''
if ($code -eq 0) {
    Write-Host 'Done. Next: run `python tools\write_issue.py --product "' -NoNewline
    Write-Host "$product" -NoNewline -ForegroundColor Cyan
    Write-Host '"`.'
} else {
    Write-Host "chat.py exited with code $code." -ForegroundColor Yellow
}
Write-Host ''
Read-Host 'Press Enter to close this window'
