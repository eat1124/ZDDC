param($a, $b)
$Response=Invoke-WebRequest -Uri $b

try{
    [System.IO.File]::WriteAllBytes($a, $Response.Content)
}catch{
   [System.Console]::WriteLine($_.Exception.Message)
}