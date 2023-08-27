import datetime as dt
import time
import tkinter as tk
from queue import Queue
from threading import Thread
from tkinter import filedialog, ttk
from tkinter.messagebox import showerror, showwarning

import serial
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from matplotlib.figure import Figure
from serial import SerialException
from serial.tools import list_ports


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # ============ Tkinter widgets variables ============== #
        self.com_combobox = None
        self.scale_lbl = None
        self.scale_v = None
        self.scale_i = None
        self.log_lbl = None
        self.log_v_input = None
        self.log_i_input = None
        self.log_period_input = None
        self.frequency = None
        self.init_btn = None
        self.load_btn = None
        self.save_btn = None
        self.status_lbl = None
        self.ax = None
        self.canvas = None
        # ============ Variables ============== #
        self.pending_init = False
        self.data_from_stream = None
        self.data_v = []
        self.data_i = []
        self.tasks_queue = Queue()
        self.sentinel_queue = Queue(maxsize=1)
        self.serial_inst = serial.Serial()
        # ============ Tkinter properties ============== #
        self.title('Trazador')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        # default screen dimensions
        window_width = 1100
        window_height = 600
        # get the screen dimension
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        # find the center point
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        # Create a centered resizable GUI window
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.create_widgets()
        # Set title and labels of axes and hide sticks
        self.plot_visibility_status(plot_status=False)
        # Schedule fist call for periodic functions
        self.com_combobox.after_idle(self.update_com_ports)
        self.after_idle(self.incoming_tasks)

    # ============ Widgets creation ============== #

    def create_widgets(self):
        """ Creates all the GUI's widgets and a figure for chart plotting """
        style = ttk.Style()
        style.configure('TButton', font=('Times New Roman', 11, 'bold'), relief='raised')
        style.configure('TLabel', font=('Times New Roman', 11))

        parent_frame = ttk.Frame(self, relief='groove')
        parent_frame.rowconfigure(0, weight=1)
        parent_frame.columnconfigure(0, weight=1, minsize=320)
        parent_frame.columnconfigure(1, weight=3)
        parent_frame.grid(row=0, column=0, sticky='NEWS')

        cmnd_frame = ttk.Frame(parent_frame, borderwidth=5, relief='groove')
        cmnd_frame.rowconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14), weight=1)
        cmnd_frame.columnconfigure(0, weight=1)
        cmnd_frame.grid(row=0, column=0, padx=3, pady=3, sticky='NEWS')

        plot_frame = ttk.Frame(parent_frame, borderwidth=5, relief='groove')
        plot_frame.rowconfigure(0, weight=9)
        plot_frame.rowconfigure(1, weight=1)
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.grid(row=0, column=1, padx=3, pady=3, sticky='NEWS')

        # ============ Command frame widgets ============ #

        ttk.Label(cmnd_frame, text='Seleccionar COM:', font=('Times New Roman', 12, 'bold')) \
            .grid(row=0, column=0, sticky='S')

        self.com_combobox = ttk.Combobox(
            cmnd_frame,
            state='readonly',
        )
        self.com_combobox.grid(row=1, column=0, sticky='NEW', pady=(5, 0), padx=70)

        self.com_combobox.bind(
            '<<ComboboxSelected>>', lambda _: self.combobox_event_on_change()
        )

        ttk.Separator(cmnd_frame, orient='horizontal').grid(
            row=2, column=0, sticky='NEWS'
        )

        self.scale_lbl = tk.StringVar()
        ttk.Label(cmnd_frame, textvariable=self.scale_lbl, font=('Times New Roman', 12, 'bold')) \
            .grid(row=3, column=0, sticky='S')
        self.scale_lbl.set('')

        self.scale_v = tk.StringVar()
        ttk.Label(cmnd_frame, textvariable=self.scale_v).grid(
            row=4, column=0
        )
        self.scale_v.set('')

        self.scale_i = tk.StringVar()
        ttk.Label(cmnd_frame, textvariable=self.scale_i).grid(
            row=5, column=0, sticky='N'
        )
        self.scale_i.set('')

        self.log_lbl = tk.StringVar()
        ttk.Label(cmnd_frame, textvariable=self.log_lbl, font=('Times New Roman', 11, 'bold')) \
            .grid(row=6, column=0, sticky='S')
        self.log_lbl.set('')

        self.log_v_input = tk.StringVar()
        ttk.Label(cmnd_frame, textvariable=self.log_v_input, font=('Times New Roman', 10)) \
            .grid(row=7, column=0, sticky='S')
        self.log_v_input.set('')

        self.log_i_input = tk.StringVar()
        ttk.Label(cmnd_frame, textvariable=self.log_i_input, font=('Times New Roman', 10)).grid(
            row=8, column=0
        )
        self.log_i_input.set('')

        self.log_period_input = tk.StringVar()
        ttk.Label(cmnd_frame, textvariable=self.log_period_input, font=('Times New Roman', 10)) \
            .grid(row=9, column=0, sticky='N')
        self.log_period_input.set('')

        ttk.Separator(cmnd_frame, orient='horizontal').grid(
            row=10, column=0, sticky='NEWS'
        )

        self.init_btn = ttk.Button(
            cmnd_frame,
            text='Iniciar',
            command=lambda: self.init_btn_method(),
            width=15,
            padding='0 3 0 3',
            state='disabled',
        )
        self.init_btn.grid(row=11, column=0, sticky='N')

        self.load_btn = ttk.Button(
            cmnd_frame,
            text='Cargar',
            command=lambda: Thread(target=self.load_file_method, daemon=True).start(),
            width=15,
            padding='0 3 0 3',
        )
        self.load_btn.grid(row=12, column=0, sticky='S')

        self.save_btn = ttk.Button(
            cmnd_frame,
            text='Guardar como...',
            command=lambda: Thread(target=self.save_file_method, daemon=True).start(),
            width=15,
            padding='0 3 0 3',
            state='disabled',
        )
        self.save_btn.grid(row=13, column=0, sticky='N', pady=(20, 0))

        ttk.Separator(cmnd_frame, orient='horizontal').grid(
            row=14, column=0, sticky='WES'
        )

        ttk.Label(cmnd_frame, text='Info...', font=('Times New Roman', 10)).grid(
            row=15, column=0, sticky='WN'
        )

        self.frequency = tk.StringVar()
        ttk.Label(cmnd_frame, textvariable=self.frequency, font=('Times New Roman', 10, 'bold')) \
            .grid(row=16, column=0, sticky='S')
        self.frequency.set('')

        self.status_lbl = tk.StringVar()
        ttk.Label(cmnd_frame, textvariable=self.status_lbl, font=('Times New Roman', 10)).grid(
            row=17, column=0, sticky='N'
        )
        self.status_lbl.set('Estado COM: DESCONECTADO')

        # ============ Plot frame widgets ============ #

        figure = Figure()
        self.ax = figure.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(figure, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky='NEWS')

        toolbar_frame = ttk.Frame(plot_frame, borderwidth=5, relief='groove')
        toolbar_frame.grid(row=1, column=0, sticky='NEWS')

        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()  # Don't know for what
        toolbar.pack(side='top', fill='both', expand=True)

    # ============ Periodic functions ============== #

    def incoming_tasks(self):
        """ Handle all incoming tasks from tasks_queue. This is
        made with the purpose to only call widgets updates from
        Tkinter main thread """
        try:
            while not self.tasks_queue.empty():
                to_run = self.tasks_queue.get()
                to_run()
        except Exception as msg:
            showerror(
                title='Error',
                message=f'Excepción desconocida.\nInfo: {msg}'
            )
            self.change_visibility_status(info_status=False, init_status=False, combo_status=False)
            self.plot_visibility_status(plot_status=False)
            if self.serial_inst.is_open:
                # If COM is already open force close thread
                self.sentinel_queue.queue.clear()
                self.sentinel_queue.put(False)
        # Highest eyes sampling rate is 60Hz, so 1/60Hz=17ms
        # 15ms should perform good and doesn't load the processor too much
        self.after(15, self.incoming_tasks)

    def update_com_ports(self):
        """ Used for update_com_ports each 1000 ms and update displayed values
        on combobox """
        available_ports = [port.description for port in list_ports.comports()]
        if not available_ports:
            if self.serial_inst.is_open:
                # This guarantees to close the thread which is idle waiting for sentinel_queue
                # for continuing to read.
                self.sentinel_queue.queue.clear()
                self.sentinel_queue.put(False)
                self.change_visibility_status(info_status=False, init_status=True, combo_status=True)
            # If there is no available port hide info labels and disable buttons
            # Restart pending init each time combo list gets empty
            self.pending_init = False
            self.com_combobox.configure(values=[])
            self.change_visibility_status(info_status=True, init_status=False, combo_status=False)
        else:
            # Sort in place available_ports by "COMx" order where x it's the number of the COM port
            available_ports.sort(key=lambda item: item.split()[-1])
            self.com_combobox.configure(values=available_ports)
        # Set another call to update_com_ports each 1000ms
        self.com_combobox.after(1000, self.update_com_ports)

    # ============ Other functions ============== #

    def combobox_event_on_change(self):
        """ Each time is selected a COM port in combobox's list, it creates a thread to
         handle the serial connection (Program guarantees that each time that is attempted to open a serial
         port it closes previously waiting threads and closes COM port) """
        self.pending_init = False
        self.change_visibility_status(info_status=False, init_status=False, combo_status=True)
        self.plot_visibility_status(plot_status=False)
        if self.serial_inst.is_open:
            # If COM is already open force close thread
            self.sentinel_queue.queue.clear()
            self.sentinel_queue.put(False)
            # It's necessary to close COM port here, otherwise raises exception
        self.pending_init = True  # Should wait for receiving first stream of data
        Thread(target=self.establish_serial_protocol, daemon=True).start()

    def init_btn_method(self):
        """ Could have two situations:
        -The User selects manually a COM port, program reads the first stream of data,
         displays it and waits for init button command
        -When is already selected a COM port User can start sequentially the whole process
        until it's completed """
        self.pending_init = False
        self.change_visibility_status(info_status=True, init_status=False, combo_status=True)
        self.plot_visibility_status(plot_status=False)
        self.frequency.set('')
        if not self.serial_inst.is_open:
            self.change_visibility_status(info_status=False, init_status=False, combo_status=True)
            Thread(target=self.establish_serial_protocol, daemon=True).start()
        self.sentinel_queue.queue.clear()
        self.after_idle(lambda: self.sentinel_queue.put(True))

    def load_file_method(self):
        """ Opens a pop-up window and asks for the .txt file location, if there is no expected
        closing operation then it proceeds to read the format file text to see if it finds an established
        file pattern, and afterwards displays the info and graphs it """
        if self.serial_inst.is_open:
            # If COM is already open force close thread
            self.sentinel_queue.queue.clear()
            self.sentinel_queue.put(False)
            self.tasks_queue.put(lambda: self.change_visibility_status(info_status=False,
                                                                       init_status=True, combo_status=True))
        filename = filedialog.askopenfilename(
            title='Seleccione archivo',
            initialdir='./',
            filetypes=(('Text files', 'txt'),),
        )
        try:
            with open(filename, mode='r') as f_obj:
                contents = f_obj.readlines()
                if (len(contents) == 514
                        and 'Archivo creado' in contents[0]
                        and 'Escalas seleccionadas:' in contents[2]
                        and 'Características de la señal' in contents[6]
                        and 'Establecida frecuencia' in contents[11]
                        and 'V(V)' and 'I(A)' in contents[13]
                ):
                    # Should clear previous values and disable init and save button
                    self.tasks_queue.put(lambda: self.change_visibility_status(info_status=False,
                                                                               init_status=False, combo_status=False))
                    strip_contents = [line.rstrip() for line in contents]
                    self.tasks_queue.put(lambda: self.scale_lbl.set(strip_contents[2]))
                    self.tasks_queue.put(lambda: self.scale_v.set(strip_contents[3]))
                    self.tasks_queue.put(lambda: self.scale_i.set(strip_contents[4]))
                    self.tasks_queue.put(lambda: self.log_lbl.set(strip_contents[6]))
                    self.tasks_queue.put(lambda: self.log_v_input.set(strip_contents[7]))
                    self.tasks_queue.put(lambda: self.log_i_input.set(strip_contents[8]))
                    self.tasks_queue.put(lambda: self.log_period_input.set(strip_contents[9]))
                    self.tasks_queue.put(lambda: self.frequency.set(strip_contents[11]))
                    self.data_from_stream = strip_contents[14:]
                    self.tasks_queue.put(lambda: self.decode_data_and_graph())
                else:
                    showerror(
                        title='Error',
                        message='El formato de los datos no es válido.'
                    )
        except FileNotFoundError:
            showwarning(
                title='Aviso',
                message='La operación ha sido abortada antes de seleccionar un archivo.',
            )

    def save_file_method(self):
        """ It saves the file with day & time format """
        default_file_name = f'{dt.datetime.now():%d_%m_%Y_%H_%M}_nombreMuestra'
        filename = filedialog.asksaveasfilename(
            title='Elija nombre del archivo',
            initialdir='./',
            filetypes=(('Text files', 'txt'),),
            initialfile=default_file_name,
            defaultextension='.txt',
        )
        try:
            with open(filename, mode='w') as f_obj:
                f_obj.write(f'Archivo creado: {dt.datetime.now():%d/%m/%Y %H:%M:%S}\n')
                f_obj.write(f"{'=' * 30}\n")
                f_obj.write(f'Escalas seleccionadas:\n')
                f_obj.write(f'{self.scale_v.get()}\n')
                f_obj.write(f'{self.scale_i.get()}\n')
                f_obj.write(f"{'=' * 30}\n")
                f_obj.write('Características de la señal:\n')
                f_obj.write(f'{self.log_v_input.get()}\n')
                f_obj.write(f'{self.log_i_input.get()}\n')
                f_obj.write(f'{self.log_period_input.get()}\n')
                f_obj.write(f"{'=' * 30}\n")
                f_obj.write(f'{self.frequency.get()}\n')
                f_obj.write(f"{'=' * 30}\n")
                f_obj.write('V(V)                 I(A)\n')
                f_obj.writelines('\n'.join(self.data_from_stream))
                f_obj.write('\n')
        except FileNotFoundError:
            showwarning(
                title='Aviso',
                message='La operación ha sido abortada antes de guardar los datos.',
            )

    def establish_serial_protocol(self):
        """ Tries to establish serial connection if there isn't a previous one, if there is one
         waits until it kills the waiting thread and opens another serial connection.
         Reads first stream of data corresponding to the first reading till
         it reaches timeout and if everything was ok, waits for init_command and then reads again
         and tries to graph the data """
        """ Every call to tkinter widgets (with the exception of errors and messages pop-ups) 
        are done through a queue which is latter checked in incoming_tasks from main thread """
        # Should wait for properly close the COM port, HW needs time to reset
        while self.serial_inst.is_open:
            pass
        # The combobox values shown are descriptions in human-readable format
        selected_com = self.com_combobox.get()
        # Remain only with the '(COMx)'
        selected_com = selected_com.split()[-1]
        # Strip parenthesis and white spaces
        selected_com = selected_com.strip(' ()')
        try:
            self.serial_inst.port = selected_com
            self.serial_inst.baudrate = 250000
            self.serial_inst.timeout = 0.7  # Blocking I/O, waits until receives smth
            self.serial_inst.write_timeout = 0.1  # Timeout to guarantee that if app fails doesn't hang
            self.serial_inst.open()
        except (SerialException, ValueError) as msg:
            showerror(
                title='Error',
                message=f'No ha sido posible abrir/configurar el puerto: {selected_com}\nInfo: {msg}',
            )
            self.tasks_queue.put(lambda: self.change_visibility_status(info_status=False,
                                                                       init_status=True, combo_status=True))
            self.plot_visibility_status(plot_status=False)
        else:
            try:
                # Should wait aprox 1s after port is opened for HW set-up time,
                # for more see: https://github.com/pyserial/pyserial/issues/329
                time.sleep(1)
                self.serial_inst.reset_input_buffer()  # Flushes input buffer in case it had smth
                first_stream_of_bytes = self.serial_inst.readlines()

                if not first_stream_of_bytes:
                    # There was no incoming data, should notify and exit
                    raise Exception('Se ha excedido el tiempo de espera de datos.\n'
                                    'Verifique que el puerto COM sea el correcto.')

                first_stream_of_strings = [line.decode('utf-8').rstrip() for line in first_stream_of_bytes]
                # Find "Escala" and "frecuencia" terms
                lst_to_display = [line for line in first_stream_of_strings if
                                  'Escala' in line or 'frecuencia' in line]

                if len(lst_to_display) != 3:
                    # There was no incoming data, should notify and exit
                    raise Exception(f'Los datos recibidos no contienen al menos uno de los siguientes términos:\n'
                                    f'* Escala (x2)\n* frecuencia (x1)\nVerifique que el puerto COM sea el correcto '
                                    f'o que el transmisor envíe correctamente los datos.')

                #  Arduino should wait for a character
                self.tasks_queue.put(lambda: self.status_lbl.set(f'Estado COM: CONECTADO a {self.serial_inst.port}'))
                self.tasks_queue.put(lambda: self.scale_lbl.set('Escalas seleccionadas:'))
                self.tasks_queue.put(lambda: self.scale_v.set(lst_to_display[0]))
                self.tasks_queue.put(lambda: self.scale_i.set(lst_to_display[1]))
                if self.pending_init:
                    self.tasks_queue.put(lambda: self.frequency.set(lst_to_display[2]))
                    self.tasks_queue.put(lambda: self.init_btn.configure(state='normal'))

                # Now should wait for "Iniciar" button or a change in combobox's list or a disconnection
                if not self.sentinel_queue.get():
                    # Even if it returns it executes finally block, so this ensures to properly close COM
                    return  # Return from thread

                self.serial_inst.write(b'S')
                self.serial_inst.reset_input_buffer()
                second_stream_of_bytes = self.serial_inst.readlines()

                if not second_stream_of_bytes:
                    # There was no incoming data, should notify and exit
                    raise Exception('No han sido recibidos datos con información sobre las mediciones.\n'
                                    'Verifique que el transmisor envíe correctamente los datos.')

                second_stream_of_strings = [line.decode('utf-8').rstrip() for line in second_stream_of_bytes]
                log_to_display = [line for line in second_stream_of_strings if
                                  'voltios' in line or 'periodo' in line]
                # These tasks could potentialy raise an Exception if data was not properly received
                # TODO what's above
                self.tasks_queue.put(lambda: self.log_lbl.set('Características de la señal:'))
                self.tasks_queue.put(lambda: self.log_v_input.set(log_to_display[0]))
                self.tasks_queue.put(lambda: self.log_i_input.set(log_to_display[1]))
                self.tasks_queue.put(lambda: self.log_period_input.set(log_to_display[2]))
                # There is no more pending init button
                pos = lst_to_display[2].find('frecuencia')
                self.tasks_queue.put(
                    lambda: self.frequency.set(f'Establecida {lst_to_display[2][pos:]}'))
                self.tasks_queue.put(
                    lambda: self.init_btn.configure(state='normal'))
                # Split values
                self.data_from_stream = second_stream_of_strings[3:503]
                data_len = len(self.data_from_stream)
                if data_len != 500:
                    raise Exception(f'Solo se recibieron N = {data_len} mediciones.\n'
                                    'Se requieren N=500.\n'
                                    'Verifique que el transmisor envíe correctamente los datos.')
                self.tasks_queue.put(lambda: self.decode_data_and_graph())
            except SerialException as msg:
                showerror(
                    title='Error',
                    message=f'Ha ocurrido un problema durante la conexión con el puerto: {selected_com}\nInfo: {msg}',
                )
                self.tasks_queue.put(lambda: self.change_visibility_status(info_status=False,
                                                                           init_status=True, combo_status=True))
            except Exception as msg:
                showerror(
                    title='Error',
                    message=f'{msg}',
                )
                self.tasks_queue.put(lambda: self.change_visibility_status(info_status=False,
                                                                           init_status=True, combo_status=True))
            else:
                # If everything went OK
                self.tasks_queue.put(lambda: self.save_btn.configure(state='normal'))
                self.tasks_queue.put(lambda: self.init_btn.configure(state='normal'))
        finally:
            # A return from thread goes straight here as well
            if self.serial_inst.is_open:
                self.serial_inst.close()
            self.tasks_queue.put(lambda: self.status_lbl.set(f'Estado COM: DESCONECTADO'))

    def decode_data_and_graph(self):
        """ This checks if data was received properly and graphs it """
        self.data_v.clear()
        self.data_i.clear()
        try:
            for value in self.data_from_stream:
                split_data = value.split()
                self.data_v.append(float(split_data[0]))
                self.data_i.append(float(split_data[1]))
        except (IndexError, ValueError) as msg:
            showerror(
                title='Error',
                message=f'Ha ocurrido un error con los datos.\nInfo: {msg}'
            )
            self.tasks_queue.put(lambda: self.change_visibility_status(info_status=False,
                                                                       init_status=True, combo_status=True))
        except Exception as msg:
            showerror(
                title='Error',
                message=f'{msg}',
            )
            self.tasks_queue.put(lambda: self.change_visibility_status(info_status=False,
                                                                       init_status=True, combo_status=True))
        else:
            self.plot_visibility_status(plot_status=True)
            self.ax.plot(self.data_v, self.data_i, '-r')
            self.canvas.draw()

    def plot_visibility_status(self, plot_status=False):
        """ Used to clean and hide/display axes during different app stages """
        self.ax.clear()
        self.ax.set_title('Caracterización I/V')
        self.ax.set_xlabel('V [V]')
        self.ax.set_ylabel('I [A]')
        self.ax.grid()
        if plot_status:
            for label in self.ax.xaxis.get_ticklabels():
                label.set_color('black')
            for label in self.ax.yaxis.get_ticklabels():
                label.set_color('black')
            self.ax.tick_params(axis='x', which='major', bottom=True)
            self.ax.tick_params(axis='y', which='major', left=True)
        else:
            for label in self.ax.xaxis.get_ticklabels():
                label.set_color('white')
            for label in self.ax.yaxis.get_ticklabels():
                label.set_color('white')
            self.ax.tick_params(axis='x', which='major', bottom=False)
            self.ax.tick_params(axis='y', which='major', left=False)

    def change_visibility_status(self, info_status=False, init_status=False, combo_status=False):
        """ Used to clean info and disable some buttons during different app stages """
        if not info_status:
            self.scale_lbl.set('')
            self.scale_v.set('')
            self.scale_i.set('')
            self.frequency.set('')
            self.log_lbl.set('')
            self.log_v_input.set('')
            self.log_i_input.set('')
            self.log_period_input.set('')
            self.save_btn.configure(state='disabled')
        if not combo_status:
            self.com_combobox.set('')
        if init_status:
            self.init_btn.configure(state='normal')
        else:
            self.init_btn.configure(state='disabled')


if __name__ == '__main__':
    app = App()
    app.mainloop()
