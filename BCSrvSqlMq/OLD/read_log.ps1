$logPath = "C:\BCSrvSqlMq\Traces\TRACE_SPB__20260301.log"
$fs = [System.IO.File]::Open($logPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
$sr = New-Object System.IO.StreamReader($fs)
$content = $sr.ReadToEnd()
$sr.Close()
$fs.Close()
Write-Output $content
