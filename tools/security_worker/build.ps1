$ErrorActionPreference = 'Stop'
$taskRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskOutput = Join-Path $taskRoot 'build/security_worker'
$taskCompiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework/v4.0.30319/csc.exe'
if (-not (Test-Path -LiteralPath $taskCompiler)) { throw 'The .NET Framework x86 C# compiler is unavailable.' }
New-Item -ItemType Directory -Path $taskOutput -Force | Out-Null
$taskExe = Join-Path $taskOutput 'SeedKeyWorker.x86.exe'
# https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/compiler-options/output#platformtarget
& $taskCompiler /nologo /target:exe /platform:x86 /optimize+ /warnaserror+ "/out:$taskExe" /r:System.Web.Extensions.dll (Join-Path $PSScriptRoot 'SeedKeyWorker.cs')
if ($LASTEXITCODE -ne 0) { throw 'Worker compilation failed.' }
Write-Output "Built mock-only x86 worker: $taskExe"
