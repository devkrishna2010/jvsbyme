Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\devkk\OneDrive\Documents\Jarvis"
WshShell.Run """C:\Users\devkk\OneDrive\Documents\Jarvis\venv\Scripts\pythonw.exe"" ""C:\Users\devkk\OneDrive\Documents\Jarvis\main.py""", 0, False

