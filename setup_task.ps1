$action = New-ScheduledTaskAction -Execute "D:\games\blog\update.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At "12:00PM"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "CatmingBlogUpdate" -Action $action -Trigger $trigger -Settings $settings -Force
Write-Host "Done. Task runs daily at 12:00."
