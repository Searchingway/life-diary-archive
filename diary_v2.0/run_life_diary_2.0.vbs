Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

appDir = fso.GetParentFolderName(WScript.ScriptFullName)
repoDir = fso.GetParentFolderName(appDir)
systemPythonw = "D:\python\pythonw.exe"
systemPython = "D:\python\python.exe"
venvPythonw = repoDir & "\.venv\Scripts\pythonw.exe"
venvPython = repoDir & "\.venv\Scripts\python.exe"

If fso.FileExists(venvPython) Then
    check = shell.Run("""" & venvPython & """ -c ""from PySide6.QtWebEngineWidgets import QWebEngineView""", 0, True)
Else
    check = 1
End If

If check = 0 And fso.FileExists(venvPythonw) Then
    pythonw = venvPythonw
ElseIf fso.FileExists(systemPythonw) Then
    pythonw = systemPythonw
Else
    pythonw = "pythonw.exe"
End If

shell.CurrentDirectory = repoDir
shell.Run """" & pythonw & """ """ & appDir & "\launcher.pyw" & """", 0, False
