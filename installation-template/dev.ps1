#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$runner = if ($env:AIXAND_DEV_PYTHON) { $env:AIXAND_DEV_PYTHON } else { 'python' }
& $runner -B (Join-Path $PSScriptRoot 'files/scripts/dev/cli.py') --project $PSScriptRoot @args
exit $LASTEXITCODE
