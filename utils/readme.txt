# Ω≈±æ
$Response=Invoke-WebRequest -Uri "http://127.0.0.1:8000/test/"

try{
    $path = Get-Location
    $path = -Join($path, '\requirements.txt')
    [System.IO.File]::WriteAllBytes($path, $Response.Content)
}catch{
   [System.Console]::WriteLine($_.Exception.Message)
}


# ÷¥––√¸¡Ó
powershell.exe -ExecutionPolicy RemoteSigned   -file "C:\Users\Administrator\Desktop\test.ps1"