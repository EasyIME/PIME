$username = $env:USERNAME
$pipeName = "PIME\Launcher"

Write-Host "Connecting to \\.\pipe\$username\$pipeName..."

try {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "$username\$pipeName", [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(5000)
    Write-Host "Connected!"
} catch {
    Write-Host "Failed to connect: $_"
    exit
}

$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

# Send init msg
$initMsg = '{"method": "init", "id": "{F80736AA-28DB-423A-92C9-5540F501C939}"}'
$writer.WriteLine($initMsg)
Write-Host "Sent init: $initMsg"

Start-Sleep -Milliseconds 500

# Send test message
$testMsg = "Hello from PowerShell Client!"
$writer.WriteLine($testMsg)
Write-Host "Sent msg: $testMsg"

Write-Host "Waiting for response..."
# Our backend manager will try to spawn "python test_backend.py"
# Since python doesn't exist, the backend manager might fail to spawn it and output an error.
# But it shouldn't crash.

if ($pipe.IsConnected) {
    # It might timeout if no reply since python is not there
    # But we can try reading
    # $reply = $reader.ReadLine()
    # Write-Host "Reply: $reply"
}

$pipe.Close()
Write-Host "Done."
