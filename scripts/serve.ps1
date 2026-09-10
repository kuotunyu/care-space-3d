param([int]$Port=8840)
$projectRoot=Split-Path -Parent $PSScriptRoot
$pythonPath=Join-Path $projectRoot '.venv\Scripts\python.exe'
if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
    throw "Port $Port is occupied; choose another port. No existing process was changed."
}
$server=Start-Process -FilePath $pythonPath -ArgumentList @('-m','http.server',"$Port",'--bind','127.0.0.1') -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectRoot 'artifacts/server.log') -RedirectStandardError (Join-Path $projectRoot 'artifacts/server-error.log')
@{pid=$server.Id;port=$Port;url="http://127.0.0.1:$Port/viewer/"} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $projectRoot 'artifacts/server.json')
Write-Output "CareSpace 3D: http://127.0.0.1:$Port/viewer/ (PID $($server.Id))"
