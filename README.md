# Requirements
- Python >= 3.10.5
- pyinstaller

# Installation
pip install -r requirements.txt


If it's needed to fix some bugs and create a new {appname}.exe copy the chart3.ico into the project's 
folder and use the following terminal command: (pyinstaller is required to build the .exe)
pyinstaller.exe --onefile --windowed --icon=chart3.ico --hidden-import pyserial --name TrazadorGUI_vVERSION main.py
