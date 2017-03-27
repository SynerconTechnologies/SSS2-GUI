import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports

import threading
import queue
import time
import string

from tkinter import tix
from tkinter.constants import *
import tkinter.scrolledtext as tkst



class SerialThread(threading.Thread):
    def __init__(self, rx_queue, tx_queue, serial_connection):
        threading.Thread.__init__(self)
        self.rx_queue = rx_queue
        self.tx_queue = tx_queue
        self.serial = serial_connection
        
    def run(self):
        try:
            while self.serial.isOpen():
                if self.serial.out_waiting ==0:
                    if self.tx_queue.qsize():
                        s = self.tx_queue.get_nowait()
                if self.serial.inWaiting():
                    line = self.serial.readline(self.serial.inWaiting())
                    self.rx_queue.put(line)
        except Exception as e:
            #print(e)
            print("Serial Connection Broken. Exiting Thread.")
            
                

class setup_serial_connections(tk.Toplevel):
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.transient(parent)
        self.title("SSS2 Connection Dialog")
        self.parent = parent
        self.result = None

        self.serial_frame = tk.Frame(self)
        self.initial_focus = self.buttonbox()
        self.serial_frame.pack(padx=5, pady=5)
        
        #self.buttonbox()
        
        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+150,
                                  parent.winfo_rooty()+150))
       

        self.initial_focus.focus_set()
        
        self.wait_window(self)

    
    def buttonbox(self):
       

        connect_button = tk.Button(self.serial_frame, text="Connect", width=10, command=self.ok, default=ACTIVE)
        connect_button.grid(row=3,column=0, padx=5, pady=5)
        cancel_button = tk.Button(self.serial_frame, text="Cancel", width=10, command=self.cancel)
        cancel_button.grid(row=3,column=1, padx=5, pady=5)
        
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        
        tk.Label(self.serial_frame,text="SSS2 COM Port").grid(row=0,column=0,columnspan=2)
        self.port_combo_box = ttk.Combobox(self.serial_frame,name="serial_port", 
                                           text="SSS2 COM Port")
        self.port_combo_box.grid(row=1,column=0,columnspan=2)
        self.find_serial_ports()
        
       

    def find_serial_ports(self):
        comPorts = []
        for possibleCOMPort in serial.tools.list_ports.comports():
            if ('Teensy' in str(possibleCOMPort)):
                comPort = str(possibleCOMPort).split() #Gets the first digits
                #print(comPort[0])
                comPorts.append(comPort[0])
        comPorts.append("Not Available")
        self.port_combo_box['values'] = comPorts
        self.port_combo_box.current(0)

        self.after(3000,self.find_serial_ports)

        
    # standard button semantics

    def ok(self, event=None):

        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()

    def cancel(self, event=None):

        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    #
    # command hooks

    def validate(self):
        if self.port_combo_box.get() == "Not Available":
            return False
        else:
            return True

    def apply(self):
        self.result=self.port_combo_box.get()
        

class SSS2(ttk.Frame):
    """The SSS2 gui and functions."""
    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        self.init_gui()
        
 
    def init_gui(self):
        """Builds GUI."""
        self.root.title('Smart Sensor Simulator Interface')

        self.pack(fill = tk.BOTH)
        #self.grid( column=0, row=0, sticky='nsew') #needed to display
       

        self.tabs = ttk.Notebook(self, name='tabs')
        self.tabs.enable_traversal()
        self.tabs.pack(fill=tk.X,padx=2, pady=2)

        ttk.Label(self, text='Synercon Technologies, LLC').pack(side='left')
        
        
        
        
        # create each Notebook tab in a Frame
        #Create a Settings Tab to amake the adjustments for sensors
        self.settings = tk.Frame(self.tabs, name='settings')
        tk.Label(self.settings,
                 text="Smart Sensor Simulator 2 Settings Adjustment").grid(row=0,
                     column=0,columnspan=2,sticky=tk.E)
        self.tabs.add(self.settings, text="SSS2 Settings") # add tab to Notebook
         

        #Create a Networks Tab to make the adjustments for J1939, CAN amd J1708
        self.networks = tk.Frame(self.tabs, name='networks')
        lab = tk.Label(self.networks,
                 text="Vehicle Newtorking").grid(row=0,column=0)
        self.tabs.add(self.networks, text="Vehicle Newtorking") # add tab to Notebook

        #Create a Connections Tab to interface with the SSS
        self.connections = tk.Frame(self.tabs, name='connections')
        tk.Label(self.connections,
                 text="SSS2 to PC Connection").grid(row=0,column=0,sticky='NSEW')
        self.tabs.add(self.connections, text="USB connection with the SSS2") # add tab to Notebook

        
        #self.serial_connect_button = tk.Button(self.connections,name="serial_connect", 
        #                                   text="Connect to SSS2", command=setup_serial_connections)   
        #self.serial_connect_button.grid(row=1,column=0,sticky="NW")

        
        self.root.option_add('*tearOff', 'FALSE')
        self.menubar = tk.Menu(self.root)
 
        self.menu_file = tk.Menu(self.menubar)
        self.menu_connection = tk.Menu(self.menubar)

        self.menu_file.add_command(label='Exit', command=self.root.quit)
        self.menu_connection.add_command(label='Select COM Port', command=self.connect_to_serial)

        self.menubar.add_cascade(menu=self.menu_file, label='File')
        self.menubar.add_cascade(menu=self.menu_connection, label='Connection')

        

        self.root.config(menu=self.menubar)

        self.serial_connected = False
        self.serial_rx_byte_list = []
        
        self.serial_interface()
        self.adjust_settings() #put this after the serial connections
       
        
    def serial_interface(self):
        self.recieved_serial_byte_count = 0

        self.connection_status_string = tk.StringVar()
        self.connection_label = tk.Label(self, textvariable=self.connection_status_string)
        self.connection_label.pack(side='right')
        
        
        self.serial_frame = tk.LabelFrame(self.connections, name="serial_console",text="SSS2 Data Display")
        self.serial_frame.grid(row=0,column=0,sticky='NSEW')

        
        
        
        
        self.text = tkst.ScrolledText(self.serial_frame, font="Courier 10" , wrap="none",
                                      height=40,width=120,padx=4,pady=4)
        self.text.grid(row=0,column=1,rowspan=9,columnspan=3,sticky=tk.W+tk.E+tk.N+tk.S )
        
        tk.Label(self.serial_frame,text="Command:").grid(row=9,column=1, sticky="E")
        
        self.serial_TX_message = ttk.Entry(self.serial_frame,width=60)
        self.serial_TX_message.grid(row=9,column = 2,sticky="EW")
        
        self.serial_TX_message.bind('<Return>',self.send_arbitrary_serial_message)

        self.serial_TX_message_button = tk.Button(self.serial_frame,name="send_serial_message", width=30,
                                           text="Send to SSS2", command=self.send_arbitrary_serial_message)
        self.serial_TX_message_button.grid(row=9,column=3,sticky="W")
        

        self.list_items_button = tk.Button(self.serial_frame,name="list_items",
                                           text="List SSS2 Settings", command=self.send_list_settings)
        self.list_items_button.grid(row=0,column=0)

        self.toggle_CAN_button = tk.Button(self.serial_frame,name="toggle_CAN",
                                           text="Toggle CAN Streaming", command=self.send_toggle_CAN)
        self.toggle_CAN_button.grid(row=1,column=0)

        self.stream_can0_box =  ttk.Checkbutton(self.serial_frame, text="Stream CAN0 (J1939)",
                                    command=self.send_stream_can0)
        self.stream_can0_box.grid(row=5,column=0,sticky="SW")
        self.stream_can0_box.state(['!alternate']) #Clears Check Box
        
        
        self.stream_can1_box =  ttk.Checkbutton(self.serial_frame, text="Stream CAN1 (E-CAN)",
                                    command=self.send_stream_can1)
        self.stream_can1_box.grid(row=6,column=0,sticky="NW")
        self.stream_can1_box.state(['!alternate']) #Clears Check Box
        
        self.serial_RX_count = ttk.Entry(self.serial_frame,width=12)
        self.serial_RX_count.grid(row=0,column = 4,sticky="NE")

        self.connect_to_serial()
        
        
    

    def connect_to_serial(self):
        connection_dialog = setup_serial_connections(self)
        self.comPort = connection_dialog.result
        if self.check_serial_connection():
            print("SSS2 already connected")
        else:
            try:
                self.serial = serial.Serial(self.comPort,baudrate=4000000,parity=serial.PARITY_ODD,timeout=0,
                                    xonxoff=False, rtscts=False, dsrdtr=False)
                global ser
                ser=self.serial
                print(self.serial)
                self.check_serial_connection()
                self.send_stream_can0()
                self.send_stream_can1()

                self.tx_queue = queue.Queue()
                self.rx_queue = queue.Queue()
                thread = SerialThread(self.rx_queue,self.tx_queue,self.serial)
                thread.start()
                self.process_serial()
                #return self.serial
            except Exception as e:
                print(e)
                self.check_serial_connection()
        
        
    def check_serial_connection(self,event = None):
        for possibleCOMPort in serial.tools.list_ports.comports():
            if ('Teensy' in str(possibleCOMPort)):
                try:
                    if self.serial.isOpen():
                        self.serial_connected = True
                        self.connection_status_string.set('SSS2 Connected on '+str(self.comPort))
                        self.text['bg']='white'
                        return True
                except Exception as e:
                    print(e)
        try:
            self.serial.close()
        except Exception as e:
            print(e)
        self.connection_status_string.set('USB to Serial Connection Unavailable. Please install drivers and plug in the SSS2.')
        self.serial_connected = False
        self.text['bg']='red'
        return False    

        

    def send_arbitrary_serial_message(self,event = None):
        commandString = self.serial_TX_message.get()
        self.send_serial(commandString)
        
    def send_serial(self,commandString):
        #self.tx_queue.put_nowait(bytes(commandString,'ascii'))
        command_bytes = bytes(commandString,'ascii') + b'\n'
        print(command_bytes)
        print(self.check_serial_connection(self))
        if self.check_serial_connection():
            self.serial.write(command_bytes)
            self.serial.flushOutput()
        
    def send_stream_can0(self):
        if self.stream_can0_box.instate(['selected']):
            commandString = "C0,1"
        else:
            commandString = "C0,0"
        self.send_serial(commandString)

    def send_stream_can1(self):
        if self.stream_can1_box.instate(['selected']):
            commandString = "C1,1"
        else:
            commandString = "C1,0"
        self.send_serial(commandString)
            
    def send_toggle_CAN(self):
        commandString = "DJ"
        self.send_serial(commandString)

    def send_list_settings(self):
        commandString = "LS"
        self.send_serial(commandString)
        
    def process_serial(self):
        gathered_bytes = len(self.serial_rx_byte_list)
        self.serial_RX_count.delete(0,tk.END)
        self.serial_RX_count.insert(0,gathered_bytes)

        if self.check_serial_connection():
            
            while self.rx_queue.qsize():
                self.serial_rx_byte_list.append(self.rx_queue.get_nowait())
                gathered_bytes = len(self.serial_rx_byte_list)
            
            if self.recieved_serial_byte_count < gathered_bytes:
                self.recieved_serial_byte_count = gathered_bytes
                if  gathered_bytes < 100:
                    display_list = self.serial_rx_byte_list
                else:
                    display_list = self.serial_rx_byte_list[gathered_bytes-100:]
                self.text.delete('1.0',tk.END)
                for line in display_list:
                    self.text.insert(tk.END, line.decode('ascii',"ignore"))
                    #self.text.insert(tk.END, '\n')
                self.text.see(tk.END)
         
        
                    

        self.after(50, self.process_serial)
    
    def adjust_settings(self):
        """Adjusts the potentiometers and other analog outputs"""
        # Button to do something on the right
        self.adjust_enable_button =  ttk.Checkbutton(self.settings, text="Enable Adjustment",
                                            command=self.send_enable_command)
        self.adjust_enable_button.grid(row=1,column=0,sticky=tk.W)
        self.adjust_enable_button.state(['!alternate']) #Clears Check Box
        self.adjust_enable = self.adjust_enable_button.instate(['selected'])

        self.potentiometer01 = potentiometer(self.settings,row=2,col=0,connector="J24:1",sss2_setting = 1,tcon_setting = 51 )
        self.potentiometer02 = potentiometer(self.settings,row=2,col=1,connector="J24:2",sss2_setting = 2,tcon_setting = 52 )
        self.potentiometer03 = potentiometer(self.settings,row=2,col=2,connector="J24:3",sss2_setting = 3,tcon_setting = 53 )
        self.potentiometer04 = potentiometer(self.settings,row=2,col=3,connector="J24:4",sss2_setting = 4,tcon_setting = 54 )
        self.potentiometer05 = potentiometer(self.settings,row=2,col=4,connector="J24:5",sss2_setting = 5,tcon_setting = 55 )
        self.potentiometer06 = potentiometer(self.settings,row=2,col=5,connector="J24:6",sss2_setting = 6,tcon_setting = 56 )
        self.potentiometer07 = potentiometer(self.settings,row=2,col=6,connector="J24:7",sss2_setting = 7,tcon_setting = 57 )
        self.potentiometer08 = potentiometer(self.settings,row=2,col=7,connector="J24:8",sss2_setting = 8,tcon_setting = 58 )
        self.potentiometer09 = potentiometer(self.settings,row=3,col=0,connector="J24:9",sss2_setting = 9,tcon_setting = 59 )
        self.potentiometer10 = potentiometer(self.settings,row=3,col=1,connector="J24:10",sss2_setting = 10,tcon_setting = 60 )
        self.potentiometer11 = potentiometer(self.settings,row=3,col=2,connector="J24:11",sss2_setting = 11,tcon_setting = 61 )
        self.potentiometer12 = potentiometer(self.settings,row=3,col=3,connector="J24:12",sss2_setting = 12,tcon_setting = 62 )
        self.potentiometer13 = potentiometer(self.settings,row=3,col=4,connector="J24:13",sss2_setting = 13,tcon_setting = 63 )
        self.potentiometer14 = potentiometer(self.settings,row=3,col=5,connector="J24:14",sss2_setting = 14,tcon_setting = 64 )
        self.potentiometer15 = potentiometer(self.settings,row=3,col=6,connector="J24:15",sss2_setting = 15,tcon_setting = 65 )
        self.potentiometer16 = potentiometer(self.settings,row=3,col=7,connector="J24:16",sss2_setting = 16,tcon_setting = 66 )
        self.potentiometer17 = potentiometer(self.settings,row=4,col=5,connector="J18:12",sss2_setting = 74,tcon_setting = 78)
        self.potentiometer18 = potentiometer(self.settings,row=4,col=6,connector="J18:13",sss2_setting = 75,tcon_setting = 79)
        self.potentiometer19 = potentiometer(self.settings,row=4,col=7,connector="J18:14",sss2_setting = 76,tcon_setting = 80)
        
    def send_enable_command(self):
        print(self.adjust_enable_button.state())
        if self.adjust_enable_button.instate(['selected']):
            print("Checked")
        else:
            print("Not Checked")          
    
    def on_quit(self):
        """Exits program."""
        self.serial.close()
        quit()

class potentiometer(SSS2):
    def __init__(self, parent, row = 2,col = 0,connector="J18:X",sss2_setting = 1,
                 tcon_setting = 51,label="Potentiometer",*args, **kwargs):
        super(SSS2,self).__init__()
        self.root = parent
        self.pot_row=row
        self.pot_col=col
        self.pot_number=sss2_setting
        self.label = label+" "+str(self.pot_number)
        self.name = self.label.lower()
        self.connector=connector
        self.tcon_setting = tcon_setting
        self.setup_potentometer()
       
          
    def setup_potentometer(self):        
        self.potentiometer_frame = tk.LabelFrame(self.root, name=self.name,text=self.label)
        self.potentiometer_frame.grid(row=self.pot_row,column=self.pot_col,sticky=tk.W)

        self.terminal_A_voltage_frame = tk.LabelFrame(self.potentiometer_frame, name='terminalAvoltage'+str(self.pot_number),text="Terminal A Voltage")
        self.terminal_A_voltage_frame.grid(row=0,column=0,columnspan=3)

        self.terminal_A_setting = tk.StringVar()
        
        
        self.twelve_volt_switch = ttk.Radiobutton(self.terminal_A_voltage_frame, text="+12V", value="+12V",
                                            command=self.send_terminal_A_voltage_command,
                                                  variable = self.terminal_A_setting)
        self.twelve_volt_switch.grid(row=0,column = 0,sticky=tk.W)
        self.twelve_volt_switch.state(['selected']) 
        
        self.five_volt_switch = ttk.Radiobutton(self.terminal_A_voltage_frame, text="+5V", value="+5V",
                                            command=self.send_terminal_A_voltage_command,
                                                variable = self.terminal_A_setting)
        self.five_volt_switch.grid(row=0,column = 1)

        tk.Label(self.terminal_A_voltage_frame,text=self.connector).grid(row=0,column=2, sticky="NE")
        
        self.other_volt_switch = ttk.Radiobutton(self.terminal_A_voltage_frame, text="Other:", value="Other",
                                                 command=self.send_terminal_A_voltage_command,
                                             variable = self.terminal_A_setting)
        self.other_volt_switch.grid(row=1,column = 0,sticky=tk.W)

        self.other_volt_value = ttk.Entry(self.terminal_A_voltage_frame,width=5)
        self.other_volt_value.grid(row=1,column = 1)

        self.other_volt_button = ttk.Button(self.terminal_A_voltage_frame,text="Set Voltage",
                                            state=tk.DISABLED,
                                            command = self.send_terminal_A_voltage_command)
        self.other_volt_button.grid(row=1,column = 2)
        
        self.terminal_A_voltage = tk.Scale(self.terminal_A_voltage_frame,
                                              from_ = 0, to = 12000, digits = 1, resolution = 100,
                                              orient = tk.HORIZONTAL, length = 180,
                                              sliderlength = 10, showvalue = 0, 
                                              label = None,
                                              command = self.set_terminal_A_voltage)
        self.terminal_A_voltage.grid(row=2,column=0,columnspan=3)

        self.terminal_A_connect_button =  ttk.Checkbutton(self.potentiometer_frame, text="Terminal A Connected",
                                            command=self.set_terminals)
        self.terminal_A_connect_button.grid(row=1,column=1,columnspan=2,sticky=tk.NW)
        self.terminal_A_connect_button.state(['!alternate']) #Clears Check Box
        self.terminal_A_connect_button.state(['selected']) 
        
        self.wiper_position_slider = tk.Scale(self.potentiometer_frame,
                                              from_ = 255, to = 0, digits = 1, resolution = 1,
                                              orient = tk.VERTICAL, length = 120,
                                              sliderlength = 10, showvalue = 0, 
                                              label = None,
                                              command = self.set_wiper_voltage)
        self.wiper_position_slider.grid(row=1,column=0,columnspan=1,rowspan=5,sticky="E")
        self.wiper_position_slider.set(50)

        tk.Label(self.potentiometer_frame,text="Wiper Position").grid(row=2,column=1, sticky="S",columnspan=2)
        self.wiper_position_value = ttk.Entry(self.potentiometer_frame,width=10)
        self.wiper_position_value.grid(row=3,column = 1,sticky="E")
        self.wiper_position_value.bind('<Return>',self.set_wiper_slider)

        self.wiper_position_button = ttk.Button(self.potentiometer_frame,text="Set Position",
                                            command = self.set_wiper_slider)
        self.wiper_position_button.grid(row=3,column = 2,sticky="W")


       
        self.wiper_connect_button =  ttk.Checkbutton(self.potentiometer_frame, text="Wiper Connected",
                                            command=self.set_terminals)
        self.wiper_connect_button.grid(row=4,column=1,columnspan=2,sticky=tk.NW)
        self.wiper_connect_button.state(['!alternate']) #Clears Check Box
        self.wiper_connect_button.state(['selected']) #checks the Box
        

        self.terminal_B_connect_button =  ttk.Checkbutton(self.potentiometer_frame,
                                                          text="Terminal B Connected",
                                                          command=self.set_terminals)
        self.terminal_B_connect_button.grid(row=5,column=1,columnspan=2,sticky=tk.SW)
        self.terminal_B_connect_button.state(['!alternate']) #Clears Check Box
        self.terminal_B_connect_button.state(['selected']) 
        
        self.set_terminals()
    def set_wiper_slider(self,event=None):
        try:
            self.wiper_position_slider.set(self.wiper_position_value.get())
            self.wiper_position_value['foreground'] = "black"
        except:
            self.root.bell()
            self.wiper_position_value['foreground'] = "red"

    def set_wiper_voltage(self,event=None):
        print(self.wiper_position_slider.get())
        self.wiper_position_value.delete(0,tk.END)
        self.wiper_position_value.insert(0,self.wiper_position_slider.get())
        commandString = "{},{}".format(self.pot_number,self.wiper_position_slider.get())
        command_bytes = bytes(commandString,'ascii') + b'\n'
        global ser
        ser.write(command_bytes)
        
    def set_terminals(self):
        self.terminal_A_connect_state = self.terminal_A_connect_button.instate(['selected'])
        self.terminal_B_connect_state = self.terminal_B_connect_button.instate(['selected'])
        self.wiper_connect_state = self.wiper_connect_button.instate(['selected'])
        terminal_setting = self.terminal_B_connect_state + 2*self.wiper_connect_state + 4*self.terminal_A_connect_state
        commandString = "{},{}".format(self.tcon_setting,terminal_setting)
        command_bytes = bytes(commandString,'ascii') + b'\n'
        global ser
        ser.write(command_bytes)
        
    def send_terminal_A_voltage_command(self):
        print(self.label,end=' ')
        print("Terminal Voltage: ",end='')
        print(self.terminal_A_setting.get())
        if self.terminal_A_setting.get() == "+12V":
            self.terminal_A_voltage.set(12000)
            self.other_volt_button['state']=tk.DISABLED
        elif self.terminal_A_setting.get() == "+5V":
            self.terminal_A_voltage.set(5000)
            self.other_volt_button['state']=tk.DISABLED
        elif self.terminal_A_setting.get() == "Other":
            self.other_volt_button.config(state=tk.NORMAL)
    
    def set_terminal_A_slider(self):
        entry_value = self.other_volt_value.get()
        #print(self.other_volt_value.config())
        self.other_volt_value['foreground'] = "black"
        try:
            print(float(entry_value))
        except ValueError:
            #print("Not a good value")
            self.root.bell()
            self.other_volt_value['foreground'] = "red"
            
    def set_terminal_A_voltage(self,scale):
        print(self.terminal_A_voltage.get())
        self.other_volt_value.delete(0,tk.END)
        self.other_volt_value.insert(0,self.terminal_A_voltage.get()/1000.0)



        


if __name__ == '__main__':

    root = tk.Tk()
    SSS2(root)
    root.mainloop()
    root.destroy() # if mainloop quits, destroy window
