# Trazador GUI

Tkinter GUI application used as a replacement for a CMD version needed to read data from an Arduino UNO R3 used to study the I/V response curve of different materials.

## Requirements

- Python >= 3.10.5

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ernvk23/plotter-uh.git
   ```
2. Navigate to the project directory:
   ```bash
   cd plotter-uh
   ```
3. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv env
   ```
   On Windows:
   ```bash
   py -m venv env
   ```
4. Activate the virtual environment:
   On Unix or macOS:
   ```bash
   source env/bin/activate
   ```
   On Windows:
   ```bash
   .\env\Scripts\activate
   ```
5. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
## Creating an Executable

To create an executable file for the application, follow these steps:
1. Navigate to the project directory.
2. Run the following command to create the executable:
   ```bash
   pyinstaller --onefile --windowed --icon=chart3.ico --hidden-import pyserial --name TrazadorGUI_vVERSION main.py
   ```
   This command will create a single-file executable named `TrazadorGUI_vVERSION.exe` (on Windows) with the provided `chart3.ico` icon, and it will automatically include the `pyserial` module.
3. The executable file will be located in the `dist` folder within the project directory.

## Usage

1. Connect your Arduino UNO R3 to your computer.
2. Run the executable `TrazadorGUI_vVERSION.exe` (on Windows) or `TrazadorGUI_vVERSION` (on other platforms).
3. Follow the instructions in the GUI to select the appropriate COM port, initialize the connection, and perform the desired actions.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with descriptive commit messages.
4. Push your changes to your forked repository.
5. Submit a pull request to the main repository.

## License

This project is licensed under the [MIT License](LICENSE.md).
