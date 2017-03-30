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

from SSS2_defaults import *

global ser
ser = False


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
                    #b = self.serial.read()
                    #self.rx_queue.put(b)
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

def all_children (wid) :
    _list = wid.winfo_children()

    for item in _list :
        if item.winfo_children() :
            _list.extend(item.winfo_children())

    return _list

class SSS2(ttk.Frame):
    """The SSS2 gui and functions."""
    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        self.settings_dict = get_default_settings()
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
         

        #Create a Networks Tab to make the adjustments for J1939, CAN and J1708
        self.networks = tk.Frame(self.tabs, name='networks')
        lab = tk.Label(self.networks,
                 text="Vehicle Newtorking").grid(row=0,column=0)
        self.tabs.add(self.networks, text="Vehicle Newtorking") # add tab to Notebook

        #Create a Connections Tab to interface with the SSS
        self.connections = tk.Frame(self.tabs, name='connections')
        tk.Label(self.connections,
                 text="SSS2 to PC Connection").grid(row=0,column=0,sticky='NSEW')
        self.tabs.add(self.connections, text="USB connection with the SSS2") # add tab to Notebook

          
        self.root.option_add('*tearOff', 'FALSE')
        self.menubar = tk.Menu(self.root)
 
        self.menu_file = tk.Menu(self.menubar)
        self.menu_connection = tk.Menu(self.menubar)

        self.menu_file.add_command(label='Open...', command=self.load_settings_file)
        self.menu_file.add_command(label='Save As...', command=self.save_settings_file)
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Exit', command=self.root.quit)
        self.menu_connection.add_command(label='Select COM Port',
                                         command=self.connect_to_serial)

        self.menubar.add_cascade(menu=self.menu_file, label='File')
        self.menubar.add_cascade(menu=self.menu_connection, label='Connection')

        

        self.root.config(menu=self.menubar)

        self.serial_connected = False
        self.serial_rx_byte_list = []
        
        self.serial_interface()
        
        self.adjust_settings() #put this after the serial connections

##        for child in all_children(self.potentiometer_bank_A):
##            #if "U1U2" in child:
##            try:
##                print(child.get())
##            except:
##                try:
##                    print(child.state())
##                except:
##                        pass

    def load_settings_file(self):
        pass
    #tkFileDialog.asksaveasfilename([options]).   
    #tkFileDialog.askopenfilename([options])
    def save_settings_file(self):
        self.settings_dict

    
    def serial_interface(self):
        self.recieved_serial_byte_count = 0

        self.connection_status_string = tk.StringVar()
        self.connection_label = tk.Label(self, textvariable=self.connection_status_string)
        self.connection_label.pack(side='right')
        
        
        self.serial_frame = tk.LabelFrame(self.connections, name="serial_console",
                                          text="SSS2 Data Display")
        self.serial_frame.grid(row=0,column=0,sticky='NSEW')

        
        
        
        
        self.text = tkst.ScrolledText(self.serial_frame, font="Courier 10" ,
                                      wrap="none", height=40,width=120,padx=4,pady=4)
        self.text.grid(row=0,column=1,rowspan=9,columnspan=3,sticky=tk.W+tk.E+tk.N+tk.S )
        
        tk.Label(self.serial_frame,text="Command:").grid(row=9,column=1, sticky="E")
        
        self.serial_TX_message = ttk.Entry(self.serial_frame,width=60)
        self.serial_TX_message.grid(row=9,column = 2,sticky="EW")
        
        self.serial_TX_message.bind('<Return>',self.send_arbitrary_serial_message)

        self.serial_TX_message_button = tk.Button(self.serial_frame,
                                            name="send_serial_message", width=30,
                                            text="Send to SSS2",
                                            command=self.send_arbitrary_serial_message)
        self.serial_TX_message_button.grid(row=9,column=3,sticky="W")
        

        self.list_items_button = tk.Button(self.serial_frame,name="list_items",
                                           text="List SSS2 Settings",
                                           command=self.send_list_settings)
        self.list_items_button.grid(row=0,column=0)

        self.toggle_CAN_button = tk.Button(self.serial_frame,name="toggle_CAN",
                                           text="Toggle CAN Streaming",
                                           command=self.send_toggle_CAN)
        self.toggle_CAN_button.grid(row=1,column=0)

        self.stream_can0_box =  ttk.Checkbutton(self.serial_frame,
                                    text="Stream CAN0 (J1939)",
                                    command=self.send_stream_can0)
        self.stream_can0_box.grid(row=5,column=0,sticky="SW")
        self.stream_can0_box.state(['!alternate']) #Clears Check Box
        
        
        self.stream_can1_box =  ttk.Checkbutton(self.serial_frame,
                                    text="Stream CAN1 (E-CAN)",
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
                self.serial = serial.Serial(self.comPort,baudrate=4000000,
                                    parity=serial.PARITY_ODD,timeout=0,
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
                        self.connection_status_string.set('SSS2 Connected on '+
                                                          str(self.comPort))
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
        self.serial_TX_message.delete(0,tk.END)
        
    def send_serial(self,commandString):
        #self.tx_queue.put_nowait(bytes(commandString,'ascii'))
        command_bytes = bytes(commandString,'ascii') + b'\n'
        print(command_bytes)
        print(self.check_serial_connection(self))
        if self.check_serial_connection():
            self.serial.write(command_bytes)
            time.sleep(.005)
        
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
                    if line[0:3]==b'CAN':
                       self.text.insert(tk.END, line[0:3].decode('ascii',"ignore"))
                       for b in line[4:]:
                          self.text.insert(tk.END," {:02X}".format(b))
                       self.text.insert(tk.END, "\n")
                    else:
                        self.text.insert(tk.END, line.decode('ascii',"ignore"))
                    #self.text.insert(tk.END, '\n')
                self.text.see(tk.END)
    
        self.after(50, self.process_serial)
    
    def adjust_settings(self):
        """Adjusts the potentiometers and other analog outputs"""
        # Button to do something on the right
        self.ignition_key_button =  ttk.Checkbutton(self.settings,
                                            text="Ignition Key Switch",
                                            command=self.send_ignition_key_command)
        self.ignition_key_button.grid(row=1,column=0,sticky=tk.W)
        self.ignition_key_button.state(['!alternate']) #Clears Check Box

        #Setup Bank A with a common Switch for Terminal A
        self.potentiometer_bank_A = tk.LabelFrame(self.settings, name="pot_bank_A",
                                                  text="Potentiometers 1 though 8")
        self.potentiometer_bank_A.grid(row=2,column=0,sticky=tk.W,rowspan=3)

        self.bankA_term_A_voltage_button =  ttk.Checkbutton(self.potentiometer_bank_A,
                                        text="Terminal A Voltage Enabled",
                                        command=self.send_bankA_term_A_voltage_command)
        self.bankA_term_A_voltage_button.grid(row=0,column=0,sticky=tk.W)
        self.bankA_term_A_voltage_button.state(['!alternate']) #Clears Check Box
        if self.settings_dict["Potentiometers"]["Group A"]["Terminal A Connection"]:
            self.bankA_term_A_voltage_button.state(['selected'])
        self.send_bankA_term_A_voltage_command() #Call the command once
        
        potpairU1U2 = potentiometer_pair(self.potentiometer_bank_A,
                           self.settings_dict["Potentiometers"]["Group A"]["Pairs"],
                           pair_id="U1U2",col=0,row=1)
        potpairU3U4 = potentiometer_pair(self.potentiometer_bank_A,
                           self.settings_dict["Potentiometers"]["Group A"]["Pairs"],
                           pair_id="U3U4",col=0,row=2)
        potpairU5U6 = potentiometer_pair(self.potentiometer_bank_A,
                           self.settings_dict["Potentiometers"]["Group A"]["Pairs"],
                           pair_id="U5U6",col=0,row=3)
        potpairU7U8 = potentiometer_pair(self.potentiometer_bank_A,
                           self.settings_dict["Potentiometers"]["Group A"]["Pairs"],
                           pair_id="U7U8",col=0,row=4)
        
        #Setup Bank B with a common Switch for Terminal A
        self.potentiometer_bank_B = tk.LabelFrame(self.settings, name="pot_bank_B",
                                                  text="Potentiometers 9 though 16")
        self.potentiometer_bank_B.grid(row=2,column=1,sticky=tk.W,rowspan=3)

        self.bankB_term_A_voltage_button =  ttk.Checkbutton(self.potentiometer_bank_B,
                                        text="Terminal A Voltage Enabled",
                                        command=self.send_bankB_term_A_voltage_command)
        self.bankB_term_A_voltage_button.grid(row=0,column=0,sticky=tk.W)
        self.bankB_term_A_voltage_button.state(['!alternate']) #Clears Check Box
        if self.settings_dict["Potentiometers"]["Group B"]["Terminal A Connection"]:
            self.bankB_term_A_voltage_button.state(['selected'])
        self.send_bankB_term_A_voltage_command() #Call the command once
        
        potpairU9U10 = potentiometer_pair(self.potentiometer_bank_B,
                           self.settings_dict["Potentiometers"]["Group B"]["Pairs"],
                           pair_id="U9U10",col=0,row=1)
        potpairU11U12 = potentiometer_pair(self.potentiometer_bank_B,
                           self.settings_dict["Potentiometers"]["Group B"]["Pairs"],
                           pair_id="U11U12",col=0,row=2)
        potpairU13U14 = potentiometer_pair(self.potentiometer_bank_B,
                           self.settings_dict["Potentiometers"]["Group B"]["Pairs"],
                           pair_id="U13U14",col=0,row=3)
        potpairU15U16 = potentiometer_pair(self.potentiometer_bank_B,
                           self.settings_dict["Potentiometers"]["Group B"]["Pairs"],
                           pair_id="U15U16",col=0,row=4)
        
        self.potentiometer_other = tk.LabelFrame(self.settings, name="pot_bank_other",
                                                 text="Potentiometers on with +5V on Terminal A")
        self.potentiometer_other.grid(row=2,column=2,sticky=tk.N)

        other_dict = self.settings_dict["Potentiometers"]["Others"]["Pairs"]["I2CPots"]["Pots"] 
        potpairU34 = potentiometer(self.potentiometer_other, other_dict["U34"], row=1, col=0)
        potpairU36 = potentiometer(self.potentiometer_other, other_dict["U36"], row=1, col=1)
        potpairU37 = potentiometer(self.potentiometer_other, other_dict["U37"], row=1, col=2)
            
        #hvadjust = potentiometer(self.potentiometer_other, other_dict["U24"], row=1, col=3)

        
        self.switch_frame = tk.Frame(self.settings, name='switch frame');
        self.switch_frame.grid(row=4,rowspan=2,column=2,sticky="NW")

        
        #Begin Switch
        self.switch_button_list=[]
        position=0
        for key in sorted(self.settings_dict["Switches"]):
            self.switch_button_list.append(config_switches(self.switch_frame,
                        self.settings_dict["Switches"],key,row=position,col=0))
            position+=1
        #End Switch

        
            
        
           
    def send_bankA_term_A_voltage_command(self):
        state=self.bankA_term_A_voltage_button.instate(['selected'])
        self.settings_dict["Potentiometers"]["Group A"]["Terminal A Connection"]=state
        if state:
            commandString = "46,1"
        else:
            commandString = "46,0"
        self.send_serial(commandString)

    def send_bankB_term_A_voltage_command(self):
        state=self.bankA_term_A_voltage_button.instate(['selected'])
        self.settings_dict["Potentiometers"]["Group B"]["Terminal A Connection"]=state
        if state:
            commandString = "74,1"
        else:
            commandString = "74,0"
        self.send_serial(commandString)
        
    def send_ignition_key_command(self):
        if self.ignition_key_button.instate(['selected']):
            commandString = "50,1"
        else:
            commandString = "50,0"
        self.send_serial(commandString)
        
    
    def on_quit(self):
        """Exits program."""
        self.serial.close()
        quit()

#class application_note(SSS2):

class config_switches(SSS2):
    def __init__(self, parent,switch_dict,key, row = 0, col = 0):
        self.root=parent
        self.switch_button_dict = switch_dict
        self.key = key
        self.col=col
        self.row=row
        
        self.setup_switches()
    def setup_switches(self):
        #key="12V Out 2"
            self.switch_button =  ttk.Checkbutton(self.root,
                                                text=self.switch_button_dict[self.key]["Label"],
                                                command=self.connect_switches)
            self.switch_button.grid(row=self.row,column=self.col,sticky=tk.W)
            self.switch_button.state(['!alternate']) #Clears Check Box
            if self.switch_button_dict[self.key]["State"]:
                self.switch_button.state(['selected'])
            else:
                self.switch_button.state(['!selected'])
            self.connect_switches()
            
    def connect_switches(self):
        state=self.switch_button.instate(['selected'])
        self.switch_button_dict[self.key]["State"]=state
        SSS2_setting = self.switch_button_dict[self.key]["SSS2 setting"]
        if state:
            commandString = "{},1".format(SSS2_setting)
        else:
            commandString = "{},0".format(SSS2_setting)
        command_bytes = bytes(commandString,'ascii') + b'\n'
        global ser
        try:
            ser.write(command_bytes)
            
        except Exception as e:
            print(e)
        return command_bytes

  
class potentiometer_pair(SSS2):
    def __init__(self, parent,pair_dict,pair_id, row = 0, col = 0):
        self.root = parent
        self.row=row
        self.col=col
        self.key=pair_id
        self.pair_dict=pair_dict[pair_id]
        self.setup_pot_pair()

    def setup_pot_pair(self):
        self.potentiometer_pair = tk.LabelFrame(self.root, name="pot_pair_"+self.key,
                                                text="Terminal A Voltage for "+self.pair_dict["Name"])
        self.potentiometer_pair.grid(row=self.row,column=self.col)

        self.terminal_A_setting = tk.StringVar()
        
        self.twelve_volt_switch = ttk.Radiobutton(self.potentiometer_pair, text="+12V", value="+12V",
                                            command=self.send_terminal_A_voltage_command,
                                                  variable = self.terminal_A_setting)
        self.twelve_volt_switch.grid(row=0,column = 0,sticky=tk.E)
        if self.pair_dict["Terminal A Voltage"] == "+12V":
            self.twelve_volt_switch.state(['selected']) 
        
        self.five_volt_switch = ttk.Radiobutton(self.potentiometer_pair, text="+5V", value="+5V",
                                            command=self.send_terminal_A_voltage_command,
                                                variable = self.terminal_A_setting)
        self.five_volt_switch.grid(row=0,column = 1,sticky=tk.W)
        if self.pair_dict["Terminal A Voltage"] == "+5V":
            self.five_volt_switch.state(['selected']) 

        self.send_terminal_A_voltage_command() #run once
        
        col_count = 0
        for key in sorted(self.pair_dict["Pots"].keys()):
            p = potentiometer(self.potentiometer_pair, self.pair_dict["Pots"][key], row=1, col=col_count)
            col_count=1

    def send_terminal_A_voltage_command(self):
        
        new_setting = self.terminal_A_setting.get()
        if new_setting == "+5V":
            commandString = "{},0".format(self.pair_dict["SSS Setting"])
        else:
            commandString = "{},1".format(self.pair_dict["SSS Setting"])
        command_bytes = bytes(commandString,'ascii') + b'\n'
        global ser
        try:
            #time.sleep(0.01)
            ser.write(command_bytes)
            
        except Exception as e:
            print(e) 

class potentiometer(SSS2):
    def __init__(self, parent, pot_dict, row = 2, col = 0):
        self.root = parent
        self.pot_row=row
        self.pot_col=col
        self.pot_settings_dict = pot_dict
        self.pot_number=self.pot_settings_dict["Port"]
        self.label = self.pot_settings_dict["Name"]
        self.name = self.label.lower()
        self.connector=self.pot_settings_dict["Pin"]
        self.tcon_setting = self.pot_settings_dict["SSS2 TCON Setting"]
        self.setup_potentometer()
      
    def setup_potentometer(self):        
        self.potentiometer_frame = tk.LabelFrame(self.root, name=self.name,text=self.label)
        self.potentiometer_frame.grid(row=self.pot_row,column=self.pot_col,sticky=tk.W)

        

        self.terminal_A_connect_button =  ttk.Checkbutton(self.potentiometer_frame, text="Terminal A Connected",
                                            command=self.set_terminals)
        self.terminal_A_connect_button.grid(row=1,column=1,columnspan=2,sticky=tk.NW)
        self.terminal_A_connect_button.state(['!alternate']) #Clears Check Box
        if self.pot_settings_dict["Term. A Connect"]:
            self.terminal_A_connect_button.state(['selected']) 
        
        self.wiper_position_slider = tk.Scale(self.potentiometer_frame,
                                              from_ = 255, to = 0, digits = 1, resolution = 1,
                                              orient = tk.VERTICAL, length = 120,
                                              sliderlength = 10, showvalue = 0, 
                                              label = None,
                                              command = self.set_wiper_voltage)
        self.wiper_position_slider.grid(row=1,column=0,columnspan=1,rowspan=5,sticky="E")
        self.wiper_position_slider.set(self.pot_settings_dict["Wiper Position"])
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
        if self.pot_settings_dict["Wiper Connect"]:
            self.wiper_connect_button.state(['selected']) #checks the Box
        

        self.terminal_B_connect_button =  ttk.Checkbutton(self.potentiometer_frame,
                                                          text="Terminal B Connected",
                                                          command=self.set_terminals)
        self.terminal_B_connect_button.grid(row=5,column=1,columnspan=2,sticky=tk.SW)
        self.terminal_B_connect_button.state(['!alternate']) #Clears Check Box
        if self.pot_settings_dict["Term. B Connect"]:
            self.terminal_B_connect_button.state(['selected']) 
        
        #print(self.set_wiper_voltage())
        #print(self.set_terminals())
        self.set_terminals()
        
    def set_wiper_slider(self,event=None):
        try:
            self.wiper_position_slider.set(self.wiper_position_value.get())
            self.wiper_position_value['foreground'] = "black"
        except:
            self.root.bell()
            self.wiper_position_value['foreground'] = "red"

    def set_wiper_voltage(self,event=None):
        self.wiper_position_value.delete(0,tk.END)
        self.wiper_position_value.insert(0,self.wiper_position_slider.get())
        commandString = "{},{}".format(self.pot_number,self.wiper_position_slider.get())
        command_bytes = bytes(commandString,'ascii') + b'\n'
        global ser
        try:
            ser.write(command_bytes)
            
        except Exception as e:
            print(e)
        return command_bytes
    
    def set_terminals(self):
        self.terminal_A_connect_state = self.terminal_A_connect_button.instate(['selected'])
        self.terminal_B_connect_state = self.terminal_B_connect_button.instate(['selected'])
        self.wiper_connect_state = self.wiper_connect_button.instate(['selected'])
        terminal_setting = self.terminal_B_connect_state + 2*self.wiper_connect_state + 4*self.terminal_A_connect_state
        commandString = "{},{}".format(self.tcon_setting,terminal_setting)
        command_bytes = bytes(commandString,'ascii') + b'\n'
        global ser
        try:
            ser.write(command_bytes)
            
        except Exception as e:
            print(e)
        return command_bytes
    
    
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

class DAC7678(SSS2):
    def __init__(self, parent,sss2_settings, row = 2, col = 0, sss2_setting = 1):
        self.root = parent
        self.row=row
        self.col=col
        self.setting_number=sss2_setting
        self.settings = current_settings
        #self.label = label+" "+str(self.pot_number)
        #self.name = self.label.lower()
        #self.connector=connector
        #self.tcon_setting = tcon_setting
        self.setup_dac_widget()
        
    def setup_dac_widget(self):
        settings = self.settings[self.setting_number]
        dac_name = settings["name"]
        
        self.dac_frame = tk.LabelFrame(self.root, name=dac_name.toLowerCase(),text=dac_name)
        self.dac_frame.grid(row=self.pot_row,column=self.pot_col,sticky=tk.W)
        
        self.mean_slider = tk.Scale(self.dac_frame,
                                              from_ = settings["Lower Limit"], to = 5000, digits = 1, resolution = 50,
                                              orient = tk.HORIZONTAL, length = 180,
                                              sliderlength = 10, showvalue = 0, 
                                              label = None,
                                              command = self.set_terminal_A_voltage)
        self.terminal_A_voltage.grid(row=2,column=0,columnspan=3)       

if __name__ == '__main__':

    root = tk.Tk()
    SSS2(root)
    root.mainloop()
    try:
        root.destroy() # if mainloop quits, destroy window
    except:
        print("Bye.")
