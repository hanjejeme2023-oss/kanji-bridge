[CmdletBinding(DefaultParameterSetName = 'Tasks')]
param(
    [Parameter(Mandatory = $true, ParameterSetName = 'Tasks')]
    [string]$Tasks,

    [Parameter(Mandatory = $true, ParameterSetName = 'Status')]
    [switch]$Status,

    [Parameter(Mandatory = $true, ParameterSetName = 'Check')]
    [switch]$Check
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$PythonPath = '<user folder>\AppData\Local\Programs\Python\Python312\python.exe'
$Generator = Join-Path $RepoRoot 'pipeline\stage4_generate.py'

Set-Location -LiteralPath $RepoRoot

foreach ($Name in @('GEMINI_API_KEY', 'GOOGLE_API_KEY')) {
    $ProcessValue = [Environment]::GetEnvironmentVariable($Name, 'Process')
    $UserValue = [Environment]::GetEnvironmentVariable($Name, 'User')
    if (-not [string]::IsNullOrWhiteSpace($ProcessValue) -or
        -not [string]::IsNullOrWhiteSpace($UserValue)) {
        throw "$Name is set at Process or User scope. Stage 4 must use Vertex AI with Application Default Credentials only. Remove it and try again."
    }
}

foreach ($Name in @('GOOGLE_CLOUD_PROJECT', 'GOOGLE_CLOUD_LOCATION', 'GOOGLE_GENAI_USE_VERTEXAI')) {
    $ProcessValue = [Environment]::GetEnvironmentVariable($Name, 'Process')
    if ([string]::IsNullOrWhiteSpace($ProcessValue)) {
        $UserValue = [Environment]::GetEnvironmentVariable($Name, 'User')
        if (-not [string]::IsNullOrWhiteSpace($UserValue)) {
            [Environment]::SetEnvironmentVariable($Name, $UserValue, 'Process')
            Write-Host "Copied User-scope setting: $Name"
        }
    }
}

if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "Python 3.12 was not found at the required path: $PythonPath"
}

if (-not ('Stage4ExecutionState' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public static class Stage4ExecutionState {
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint SetThreadExecutionState(uint executionState);
}
'@
}

function Invoke-Stage4Python {
    param([string[]]$Arguments)
    & $PythonPath $Generator @Arguments | Out-Host
    return $LASTEXITCODE
}

$ES_CONTINUOUS = [uint32]2147483648
$ES_SYSTEM_REQUIRED = [uint32]0x00000001
$ExitCode = 0

try {
    $KeepAwakeResult = [Stage4ExecutionState]::SetThreadExecutionState(
        $ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED
    )
    if ($KeepAwakeResult -eq 0) {
        throw 'Windows refused the keep-awake request.'
    }

    if ($Status) {
        $ExitCode = Invoke-Stage4Python @('--status')
    }
    elseif ($Check) {
        $ExitCode = Invoke-Stage4Python @('--check')
        if ($ExitCode -eq 0) {
            $ExitCode = Invoke-Stage4Python @('--status')
        }
    }
    else {
        $TaskNumbers = @(
            $Tasks.Split(',') |
                ForEach-Object { $_.Trim() } |
                Where-Object { $_ -ne '' }
        )
        if ($TaskNumbers.Count -eq 0) {
            throw '-Tasks must contain one or more task numbers (1, 2, 3 or 4).'
        }
        foreach ($TaskNumber in $TaskNumbers) {
            if ($TaskNumber -notmatch '^[1-4]$') {
                throw "Invalid task '$TaskNumber'. Use only 1, 2, 3 or 4."
            }
        }

        :TaskLoop foreach ($TaskNumber in $TaskNumbers) {
            for ($Attempt = 1; $Attempt -le 3; $Attempt++) {
                Write-Host "Starting task $TaskNumber (launcher attempt $Attempt of 3)"
                $ExitCode = Invoke-Stage4Python @('--task', $TaskNumber)
                if ($ExitCode -eq 0) {
                    continue TaskLoop
                }
                if ($Attempt -lt 3) {
                    Write-Host "Task $TaskNumber exited with code $ExitCode; waiting 120 seconds before resume."
                    Start-Sleep -Seconds 120
                }
            }
            [Console]::Error.WriteLine(
                "Task $TaskNumber still failed after 3 launcher attempts; no later task was started."
            )
            $ExitCode = Invoke-Stage4Python @('--status')
            if ($ExitCode -eq 0) {
                $ExitCode = 1
            }
            break
        }
        if ($ExitCode -eq 0) {
            $ExitCode = Invoke-Stage4Python @('--status')
        }
    }
}
finally {
    [void][Stage4ExecutionState]::SetThreadExecutionState($ES_CONTINUOUS)
}

exit $ExitCode
