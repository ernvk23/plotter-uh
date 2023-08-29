Tkinter GUI application used as a replacement for a CMD version needed to read data from an Arduino UNO R3 used to study the I/V response curve of different materials.

# Requirements
- Python >= 3.10.5

# Installation
pip install -r requirements.txt

# Creating another .exe
pyinstaller.exe --onefile --windowed --icon=chart3.ico --hidden-import pyserial --name TrazadorGUI_vVERSION main.py
