Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\speaker project"
WshShell.Run """" & "D:\speaker project\.venv\Scripts\pythonw.exe" & """ """ & "D:\speaker project\app.py" & """", 0, False
