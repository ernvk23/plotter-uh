main.py was created using Python 3.10.5, so keep it in mind for compatibility issues.

Aditional packages required to run the main.py file:
* pyserial
* matplotlib


If it's needed to fix some bugs and create a new .exe copy the chart3.ico into the project's 
folder and use the following terminal command: (pyinstaller is required to build the .exe)
pyinstaller.exe --onefile --windowed --icon=chart3.ico --hidden-import pyserial --name TrazadorGUI_vVERSION main.py