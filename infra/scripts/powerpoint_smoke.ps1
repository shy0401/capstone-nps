$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location -LiteralPath $taskRoot
$pptCheck = New-Object -ComObject PowerPoint.Application
$initialPresentations = $pptCheck.Presentations.Count
$samplePath = (Resolve-Path 'test-results/samples/golden-synthetic.pptx').Path
$renderPath = Join-Path $taskRoot 'test-results/powerpoint-render'
New-Item -ItemType Directory -Path $renderPath -Force | Out-Null
try {
    $checkedDeck = $pptCheck.Presentations.Open($samplePath, -1, 0, 0)
    $checkedDeck.Export($renderPath, 'PNG', 1600, 900)
    @{status='PASS'; application='Microsoft PowerPoint'; slides=$checkedDeck.Slides.Count; opened_read_only=$true; export='PNG'; sha256=(Get-FileHash -LiteralPath $samplePath -Algorithm SHA256).Hash.ToLower()} | ConvertTo-Json | Set-Content -Encoding UTF8 'test-results/powerpoint-smoke.json'
} finally {
    if ($null -ne $checkedDeck) { $checkedDeck.Close() }
    if ($initialPresentations -eq 0 -and $pptCheck.Presentations.Count -eq 0) { $pptCheck.Quit() }
    if ($null -ne $checkedDeck) { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($checkedDeck) | Out-Null }
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pptCheck) | Out-Null
}
Get-Content 'test-results/powerpoint-smoke.json'
