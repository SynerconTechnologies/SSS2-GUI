import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports

import threading
import queue
import time
import string

from tkinter.tix import *
from tkinter.constants import *
import tkinter.scrolledtext as tkst

from SSS2_defaults import *

global ser
ser = False


class SerialThread(threading.Thread):
    def __init__(self, rx_queue, tx_queue):
        threading.Thread.__init__(self)
        self.rx_queue = rx_queue
        self.tx_queue = tx_queue
        
    def run(self):
        global ser
        try:
            while ser.isOpen():
                if self.tx_queue.qsize():
                    s = self.tx_queue.get_nowait()
                if ser.inWaiting():
                    line = ser.readline()
                    self.rx_queue.put(line)
                    #b = self.serial.read()
                    #self.rx_queue.put(b)
        except Exception as e:
            #print(e)
            print("Serial Connection Broken. Exiting Thread.")
            setup_serial_connections(mainwindow)
            
                

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
       

        connect_button = tk.Button(self.serial_frame, name='connect_button',
                                   text="Connect", width=10, command=self.ok, default=ACTIVE)
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
                comPorts.append(comPort[0])
        comPorts.append("Not Available")
        self.port_combo_box['values'] = comPorts
        self.port_combo_box.current(0)

        self.after(2000,self.find_serial_ports)

        
    # standard button semantics

    def ok(self, event=None):

        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        

        self.cancel()

    def cancel(self, event=None):
        self.apply() #usually this is in the OK function
        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    #
    # command hooks

    def validate(self):
        if self.port_combo_box.get() == "Not Available":
            return False
        else:
            try:
                global ser
                ser = serial.Serial(self.port_combo_box.get(),baudrate=4000000,
                                    parity=serial.PARITY_ODD,timeout=0,
                                    xonxoff=False, rtscts=False, dsrdtr=False)
                print(ser)
                return True
            except Exception as e:
                print(e)
                try:
                    ser.close()
                except Exception as e:
                    print(e)
                #TODO raise an error window
                return False

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
        self.frame_top = ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        self.root.geometry('+0+0')
        self.settings_dict = get_default_settings()
        self.root.title('Smart Sensor Simulator Interface')
        self.grid( column=0, row=0, sticky='NSEW') #needed to display
        
        self.init_gui()
        
 
    def init_gui(self):
        """Builds GUI."""
        

        self.tx_queue = queue.Queue()
        self.rx_queue = queue.Queue()

        # Button to do something on the right
        self.ignition_key_button =  ttk.Checkbutton(self,name='ignition_key_switch',
                                            text="Ignition Key Switch",
                                            command=self.send_ignition_key_command)
        self.ignition_key_button.grid(row=0,column=0,sticky=tk.W)
        self.ignition_key_button.state(['!alternate']) #Clears Check Box
        
        
        ttk.Label(self, text='USB/Serial Monitor:').grid(row=0,column=1,sticky=tk.E)
        self.serial_rx_entry = tk.Entry(self,width=60,name='serial_monitor')
        self.serial_rx_entry.grid(row=0,column=2,sticky=tk.W+tk.E)
        
        self.tabs = ttk.Notebook(self, name='tabs')
        self.tabs.enable_traversal()
        self.tabs.grid(row=1,column=0,columnspan=3,sticky=tk.W)
        
        ttk.Label(self, text='Synercon Technologies, LLC',name='synercon_label').grid(row=2,column=0,sticky=tk.W)
        
        # create each Notebook tab in a Frame
        #Create a Settings Tab to amake the adjustments for sensors
        self.settings_tab = tk.Frame(self.tabs, name='potentiometer_tab')
        self.tabs.add(self.settings_tab, text="Digital Potentiometers") # add tab to Notebook
         

        #Create a Voltage out make the adjustments for PWM, DAC, and Regulators
        self.voltage_out_tab = tk.Frame(self.tabs, name='voltage_out_tab')
        self.tabs.add(self.voltage_out_tab, text="Voltage Output") # add tab to Notebook

        #Create a Networks Tab to make the adjustments for J1939, CAN and J1708
        self.truck_networks_tab = tk.Frame(self.tabs, name='truck_network_tab')
        self.tabs.add(self.truck_networks_tab, text="Vehicle Networks") # add tab to Notebook

        #Create a Connections Tab to interface with the SSS
        self.connections = tk.Frame(self.tabs, name='usb_serial_connections')
        self.tabs.add(self.connections, text="USB/Serial Interface") # add tab to Notebook

          
        self.root.option_add('*tearOff', 'FALSE')
        self.menubar = tk.Menu(self.root,name='main_menus')
 
        self.menu_file = tk.Menu(self.menubar)
        self.menu_connection = tk.Menu(self.menubar)

        self.menu_file.add_command(label='Open...', command=self.load_settings_file)
        self.menu_file.add_command(label='Save As...', command=self.save_settings_file)
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Reset to Defaults', command=self.init_tabs)
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Exit', command=self.root.quit)
        self.menu_connection.add_command(label='Select COM Port',
                                         command=self.connect_to_serial)

        self.menubar.add_cascade(menu=self.menu_file, label='File')
        self.menubar.add_cascade(menu=self.menu_connection, label='Connection')

        

        self.root.config(menu=self.menubar)

        self.serial_connected = False
        self.serial_rx_byte_list = []
        self.received_can0_messages=[]
        self.received_can1_messages=[]
        self.received_can2_messages=[]
        self.received_j1708_messages=[]
        self.init_tabs()
        
    def init_tabs(self):
                
        self.serial_interface()
        thread = SerialThread(self.rx_queue,self.tx_queue)
        thread.start()
        self.process_serial()
        
        self.potentiometer_settings() #put this after the serial connections

        self.voltage_out_settings()

        self.vehicle_networks_settings()
        

    def open_settings_file(self):
        #tkFileDialog.askopenfilename([options])
        pass
    def load_settings_file(self):
        self.settings_dict["Potentiometers"][bank_key]["Terminal A Connection"]=state
        
    
    def saveas_settings_file(self):
        #tkFileDialog.asksaveasfilename([options]).
        pass

    def save_settings_file(self):
        group = self.settings_dict["Potentiometers"]["Group A"]
        group["Terminal A Connection"] = self.bankA_term_A_voltage_button.instate(['selected'])

        pair = group["Pairs"]["U1U2"]
        if self.potpairU1U2.twelve_volt_switch.instate(['selected']):
            pair["Terminal A Voltage"] = "+12V"
        else:
            pair["Terminal A Voltage"] = "+5V"
        pot = pair["Pots"]["U1"]
        pot["Term. A Connect"] =  self.potpairU1U2.pots["U1"].terminal_A_connect_button.instate(['selected']) 
        pot["Term. B Connect"] =  self.potpairU1U2.pots["U1"].terminal_B_connect_button.instate(['selected']) 
        pot["Wiper Connect"] =  self.potpairU1U2.pots["U1"].wiper_connect_button.instate(['selected']) 
        pot["Wiper Position"] = int(self.potpairU1U2.pots["U1"].wiper_position_slider.get())
        pot["ECU Pins"] = self.potpairU1U2.pots["U1"].ecu_app.ecu_pins.get()
        pot["Application"] = self.potpairU1U2.pots["U1"].ecu_app.ecu_app.get()
        

        filename='SSS2settings.json'
        with open(filename,'w') as outfile:
            json.dump(self.settings_dict,outfile,indent=4)
        print("Saved "+filename)
        
    def vehicle_networks_settings(self):
       
        self.preset_message_frame = tk.LabelFrame(self.truck_networks_tab, name="preset CAN Messages",
                                                  text="Preset CAN Messages")
        self.preset_message_frame.grid(row=0,column=0,sticky="NW",columnspan=1)

        
        
        self.message_config_frame = tk.LabelFrame(self.truck_networks_tab, name="network Configurations",
                                                  text="Network Configurations")
        self.message_config_frame.grid(row=0,column=1,sticky="NW",columnspan=1)

        lin_to_shield_switch = config_switches(self.message_config_frame,
                            self.settings_dict["Switches"],"LIN to SHLD",row=0,col=0)
        lin_to_port_16 = config_switches(self.message_config_frame,
                            self.settings_dict["Switches"],"LIN to Port 16",row=1,col=0)
        lin_to_master = config_switches(self.message_config_frame,
                            self.settings_dict["Switches"],"LIN Master Pullup Resistor",row=2,col=0)
        can0_term = config_switches(self.message_config_frame,
                            self.settings_dict["Switches"],"CAN0",row=3,col=0)
        can1_term = config_switches(self.message_config_frame,
                            self.settings_dict["Switches"],"CAN1",row=5,col=0)
        can2_term = config_switches(self.message_config_frame,
                            self.settings_dict["Switches"],"CAN2",row=4,col=0)
        
    def voltage_out_settings(self):
       
        self.DAC_bank = tk.LabelFrame(self.voltage_out_tab, name="dac_bank",
                                                  text="Voltage Outputs")
        self.DAC_bank.grid(row=0,column=0,sticky="NW",columnspan=1)

        dac_dict=self.settings_dict["DACs"]
        Vout2A = DAC7678(self.DAC_bank, dac_dict["Vout1"], row=0, col=0)
        Vout2B = DAC7678(self.DAC_bank, dac_dict["Vout2"], row=0, col=1)
        Vout2C = DAC7678(self.DAC_bank, dac_dict["Vout3"], row=0, col=2)
        Vout2D = DAC7678(self.DAC_bank, dac_dict["Vout4"], row=0, col=3)
        Vout2E = DAC7678(self.DAC_bank, dac_dict["Vout5"], row=1, col=0)
        Vout2F = DAC7678(self.DAC_bank, dac_dict["Vout6"], row=1, col=1)
        Vout2G = DAC7678(self.DAC_bank, dac_dict["Vout7"], row=1, col=2)
        Vout2H = DAC7678(self.DAC_bank, dac_dict["Vout8"], row=1, col=3)

        vout2a_switch = config_radio_switches(self.DAC_bank,
                            self.settings_dict["Switches"],"Port 10 or 19",rowA=2,colA=1,rowB=3,colB=1)
        vout2b_switch = config_radio_switches(self.DAC_bank,
                            self.settings_dict["Switches"],"Port 15 or 18",rowA=2,colA=0,rowB=3,colB=0)
        
        self.hvadjout_bank = tk.LabelFrame(self.voltage_out_tab, name="hvadjout_bank",
                                                  text="High Current Adjustable Regulator")
        self.hvadjout_bank.grid(row=1,column=0,sticky="N",columnspan=1)
        hvadjout = DAC7678(self.hvadjout_bank, dac_dict["HVAdjOut"], row=0, col=0)
        
        self.pwm_bank=tk.LabelFrame(self.voltage_out_tab, name="pwm_bank",
                                                  text="Pulse Width Modulated Outputs")
        self.pwm_bank.grid(row=2,column=0,sticky="NW",columnspan=1)

        pwm1_switch = config_switches(self.pwm_bank,
                            self.settings_dict["Switches"],"PWM1 Connect",row=1,col=0)
        pwm2_switch = config_switches(self.pwm_bank,
                            self.settings_dict["Switches"],"PWM2 Connect",row=1,col=1)
        pwm3_switch = config_radio_switches(self.pwm_bank,
                            self.settings_dict["Switches"],"PWM3 or 12V",rowA=1,colA=2,rowB=2,colB=2)
        
        pwm4_switch = config_radio_switches(self.pwm_bank,
                            self.settings_dict["Switches"],"PWM4 or Ground",rowA=1,colA=3,rowB=2,colB=3)
        
        pwm12_switch = config_radio_switches(self.pwm_bank,
                            self.settings_dict["Switches"],"PWMs or CAN2",rowA=2,colA=0,rowB=3,colB=0)
        
        pwm_dict=self.settings_dict["PWMs"]
        PWM1 = pwm_out(self.pwm_bank, pwm_dict["PWM1"], row=0, col=0)
        PWM2 = pwm_out(self.pwm_bank, pwm_dict["PWM2"], row=0, col=1)
        PWM3 = pwm_out(self.pwm_bank, pwm_dict["PWM3"], row=0, col=2)
        PWM4 = pwm_out(self.pwm_bank, pwm_dict["PWM4"], row=0, col=3)
        
    def serial_interface(self):
        self.recieved_serial_byte_count = 0

        self.connection_status_string = tk.StringVar(name='status_string')
        self.connection_label = tk.Label(self, textvariable=self.connection_status_string,name="connection_label")
        self.connection_label.grid(row=2,column=2,sticky="E")
             
        self.serial_frame = tk.LabelFrame(self.connections, name="serial_console",
                                          text="SSS2 Data Display")
        self.serial_frame.grid(row=0,column=0,sticky='NSEW')
        self.text = tkst.ScrolledText(self.serial_frame, font="Courier 10" ,
                                      height=50,width=140,padx=4,pady=4)
        self.text.grid(row=0,column=1,rowspan=9,columnspan=3,sticky=tk.W+tk.E+tk.N+tk.S )
    
        self.serial_RX_count = ttk.Entry(self.serial_frame,width=12)
        self.serial_RX_count.grid(row=0,column = 4,sticky="NE")

        self.connect_to_serial()
        
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
        self.send_stream_can0()
        
        self.stream_can1_box =  ttk.Checkbutton(self.serial_frame,
                                    name="stream CAN2 (E-CAN)",
                                    text="Stream CAN2 (E-CAN)",
                                    command=self.send_stream_can1)
        self.stream_can1_box.grid(row=6,column=0,sticky="NW")
        self.stream_can1_box.state(['!alternate']) #Clears Check Box
        self.send_stream_can1()

        
        self.stream_A21_box =  ttk.Checkbutton(self.serial_frame,
                                    name='stream_A21',
                                    text="Stream Port 10 Voltage Readings",
                                    command=self.send_stream_A21)
        self.stream_A21_box.grid(row=5,column=0,sticky="NW")
        self.stream_A21_box.state(['!alternate']) #Clears Check Box
        self.send_stream_A21()

        self.serial_window_lines = 500
        
    def send_stream_A21(self):
        if self.stream_A21_box.instate(['selected']):
            commandString = "SV,1"
        else:
            commandString = "SV,0"
        send_serial_command(commandString)    
        
    

    def connect_to_serial(self):
        connection_dialog = setup_serial_connections(self)
        self.comPort = connection_dialog.result
        if self.check_serial_connection():
            print("SSS2 already connected")
        else:
            try:
                self.check_serial_connection()
            except Exception as e:
                print(e)
                self.check_serial_connection()
        
        
    def check_serial_connection(self,event = None):
        
        global ser
        for possibleCOMPort in serial.tools.list_ports.comports():
            if ('Teensy' in str(possibleCOMPort)):
                try:
                    if ser.isOpen():
                        self.serial_connected = True
                        self.connection_status_string.set('SSS2 Connected on '+
                                                          str(self.comPort))
                        self.text['bg']='white'
                        self.serial_rx_entry['bg']='white'
                        return True
                except Exception as e:
                    print(e)
                    setup_serial_connections(self)
        try:
            ser.close()
        except Exception as e:
            print(e)
        self.connection_status_string.set('USB to Serial Connection Unavailable. Please install drivers and plug in the SSS2.')
        self.serial_connected = False
        self.text['bg']='red'
        self.serial_rx_entry['bg']='red'
        
        return False    
        
        
    def send_arbitrary_serial_message(self,event = None):
        commandString = self.serial_TX_message.get()
        send_serial_command(commandString)
        self.serial_TX_message.delete(0,tk.END)
        
        
    def send_stream_can0(self):
        if self.stream_can0_box.instate(['selected']):
            commandString = "C0,1"
        else:
            commandString = "C0,0"
        send_serial_command(commandString)

    def send_stream_can1(self):
        if self.stream_can1_box.instate(['selected']):
            commandString = "C1,1"
        else:
            commandString = "C1,0"
        send_serial_command(commandString)
            
    def send_toggle_CAN(self):
        commandString = "DJ"
        send_serial_command(commandString)

    def send_list_settings(self):
        commandString = "LS"
        send_serial_command(commandString)
        
    def process_serial(self):
        gathered_bytes = len(self.serial_rx_byte_list)
        self.serial_RX_count.delete(0,tk.END)
        self.serial_RX_count.insert(0,gathered_bytes)

        if self.check_serial_connection():
            
            while self.rx_queue.qsize():
                new_serial_line = self.rx_queue.get_nowait()
                self.serial_rx_byte_list.append(new_serial_line)
                gathered_bytes = len(self.serial_rx_byte_list)
                if new_serial_line[0:3]==b'CAN 0':
                    self.received_can0_messages.append(new_serial_line)
                elif new_serial_line[0:3]==b'CAN 1':
                    self.received_can2_messages.append(new_serial_line)
            if self.recieved_serial_byte_count < gathered_bytes:
                self.recieved_serial_byte_count = gathered_bytes
                if  gathered_bytes < self.serial_window_lines:
                    display_list = self.serial_rx_byte_list
                else:
                    display_list = self.serial_rx_byte_list[gathered_bytes-self.serial_window_lines:]
                self.text.delete('1.0',tk.END)
                for line in display_list:
                    self.text.insert(tk.END, line.decode('ascii',"ignore"))
                self.text.see(tk.END)
                self.serial_rx_entry.delete(0,tk.END)
                self.serial_rx_entry.insert(0, self.serial_rx_byte_list[-1].decode('ascii',"ignore"))
    
        self.after(50, self.process_serial)
    
    def potentiometer_settings(self):
        """Adjusts the potentiometers and other analog outputs"""

        self.pot_bank={}
        self.bank_button={}
        row_index=0
        for self.bank_key in sorted(self.settings_dict["Potentiometers"]):
            #Setup Bank with a common Switch for Terminal A
            label=self.settings_dict["Potentiometers"][self.bank_key]["Label"]
            self.pot_bank[self.bank_key] = tk.LabelFrame(self.settings_tab,
                                                    name=label.lower(),
                                                    text=label)
            self.pot_bank[self.bank_key].grid(row=row_index,column=0,sticky=tk.W,columnspan=3)
            if self.settings_dict["Potentiometers"][self.bank_key]["Terminal A Connection"]:
                self.bank_button[self.bank_key] =  ttk.Checkbutton(self.pot_bank[self.bank_key],
                                                    text="Terminal A Voltage Enabled",
                                                    name='terminal_A_voltage_connect',
                                                    command=self.send_bank_term_A_voltage_command)
                self.bank_button[self.bank_key].grid(row=0,column=0,sticky=tk.W)
                self.bank_button[self.bank_key].state(['!alternate']) #Clears Check Box
                if self.settings_dict["Potentiometers"][self.bank_key]["Terminal A Connection"]:
                    self.bank_button[self.bank_key].state(['selected'])
                self.send_bank_term_A_voltage_command() #Call the command once

            self.potpair={}
            col_index=0
            for key in sorted(self.settings_dict["Potentiometers"][self.bank_key]["Pairs"]):
                self.potpair[key] = potentiometer_pair(self.pot_bank[self.bank_key],
                               self.settings_dict["Potentiometers"][self.bank_key]["Pairs"],
                               pair_id=key,col=col_index,row=1)
                col_index += 1
            row_index += 1
 
        self.settings_tab.grid_columnconfigure(1,weight=2)
        self.switch_frame = tk.Frame(self.settings_tab, name='switch frame');
        self.switch_frame.grid(row=2,rowspan=1,column=1, columnspan=1,sticky="NE")

        
        self.twelve2_switch = config_switches(self.switch_frame,
                            self.settings_dict["Switches"],"12V Out 2",row=0,col=0)
        self.ground2_switch = config_switches(self.switch_frame,
                            self.settings_dict["Switches"],"Ground Out 2",row=1,col=0)
        
        
        angled_photo = tk.PhotoImage(file="sss2angle.gif")
        new_photo = angled_photo.subsample(2,2)
        
        image_label = Label(self.settings_tab,image=new_photo)
        image_label.image = new_photo
        image_label.grid(row=2,column=2,sticky=tk.E)

           
    def send_bank_term_A_voltage_command(self):
        state=self.bank_button[self.bank_key].instate(['selected'])
        setting = self.settings_dict["Potentiometers"][self.bank_key]["SSS2 Setting"]
        if setting is not None:
            if state:
                commandString = "{:d},1".format(setting)
            else:
                commandString = "{:d},0".format(setting)
            send_serial_command(commandString)

    def send_ignition_key_command(self):
        if self.ignition_key_button.instate(['selected']):
            commandString = "50,1"
        else:
            commandString = "50,0"
        send_serial_command(commandString)
        
    
    def on_quit(self):
        """Exits program."""
        self.serial.close()
        quit()

#class pot_bank(SSS2):
    

class config_switches(SSS2):
    def __init__(self, parent,switch_dict,key, row = 0, col = 0):
        self.root=parent
        self.switch_button_dict = switch_dict
        self.key = key
        self.col=col
        self.row=row
        self.setup_switches()

    def setup_switches(self):
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
        return send_serial_command(commandString)

class config_radio_switches(SSS2):
    def __init__(self, parent,switch_dict,key, rowA = 0, colA = 0,
                 rowB = 0, colB = 1, rowspanA=2, rowspanB=2,
                 colspanA=1, colspanB=1,):
        self.root=parent
        self.switch_button_dict = switch_dict
        self.key = key
        self.colA=colA
        self.rowA=rowA
        self.colB=colB
        self.rowB=rowB
        self.labelA=self.switch_button_dict[self.key]["Label A"]
        self.nameA=self.labelA.lower()
        self.labelB=self.switch_button_dict[self.key]["Label B"]
        self.nameB=self.labelB.lower()
        self.setup_switches()

    def setup_switches(self):
        button_val = tk.StringVar()
        
        self.switch_buttonA =  ttk.Radiobutton(self.root,
                                               text=self.labelA,
                                               value = "A",
                                               name=self.nameA,
                                               command=self.connect_switches,
                                               variable=button_val)
        
        self.switch_buttonA.grid(row=self.rowA,column=self.colA,sticky=tk.W,columnspan=2)
        self.switch_buttonA.state(['!alternate']) #Clears Check Box
        if self.switch_button_dict[self.key]["State"]:
            self.switch_buttonA.state(['selected'])
        else:
            self.switch_buttonA.state(['!selected'])

        self.switch_buttonB =  ttk.Radiobutton(self.root,
                                               text=self.labelB,
                                               value = "B",
                                               name=self.nameB,
                                               command=self.connect_switches,
                                               variable=button_val)
        self.switch_buttonB.grid(row=self.rowB,column=self.colB,sticky=tk.W,columnspan=2)
        self.switch_buttonB.state(['!alternate']) #Clears Check Box
        if not self.switch_button_dict[self.key]["State"]:
            self.switch_buttonB.state(['selected'])
        else:
            self.switch_buttonB.state(['!selected'])

        self.connect_switches()
            
    def connect_switches(self):
        state=self.switch_buttonA.instate(['selected'])
        self.switch_button_dict[self.key]["State"]=state
        SSS2_setting = self.switch_button_dict[self.key]["SSS2 setting"]
        if state:
            commandString = "{},1".format(SSS2_setting)
        else:
            commandString = "{},0".format(SSS2_setting)
        return send_serial_command(commandString)   

  
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
                                                text=self.pair_dict["Name"])
        self.potentiometer_pair.grid(row=self.row,column=self.col)
        if self.pair_dict["Terminal A Voltage"]:
            self.terminal_A_setting = tk.StringVar()
            
            self.twelve_volt_switch = ttk.Radiobutton(self.potentiometer_pair, text="+12V", value="+12V",
                                                command=self.send_terminal_A_voltage_command,
                                                      name='button_12',
                                                      variable = self.terminal_A_setting)
            self.twelve_volt_switch.grid(row=0,column = 0,sticky=tk.E)
            if self.pair_dict["Terminal A Voltage"] == "+12V":
                self.twelve_volt_switch.state(['selected']) 
            
            self.five_volt_switch = ttk.Radiobutton(self.potentiometer_pair, text="+5V", value="+5V",
                                                command=self.send_terminal_A_voltage_command,
                                                    name='button_5',
                                                    variable = self.terminal_A_setting)
            self.five_volt_switch.grid(row=0,column = 1,sticky=tk.W)
            if self.pair_dict["Terminal A Voltage"] == "+5V":
                self.five_volt_switch.state(['selected']) 

            self.send_terminal_A_voltage_command() #run once
        
        col_count = 0
        self.pots={}
        for key in sorted(self.pair_dict["Pots"].keys()):
            self.pots[key] = potentiometer(self.potentiometer_pair, self.pair_dict["Pots"][key], row=1, col=col_count)
            col_count+=1

    def send_terminal_A_voltage_command(self):
        
        new_setting = self.terminal_A_setting.get()
        if new_setting == "+5V":
            commandString = "{},0".format(self.pair_dict["SSS Setting"])
        else:
            commandString = "{},1".format(self.pair_dict["SSS Setting"])
        return send_serial_command(commandString)

class potentiometer(SSS2):
    def __init__(self, parent, pot_dict, row = 2, col = 0):
        self.root = parent
        self.pot_row=row
        self.pot_col=col
        self.pot_settings_dict = pot_dict
        self.pot_number=self.pot_settings_dict["SSS2 Wiper Setting"]
        self.connector=self.pot_settings_dict["Pin"]
        self.label = self.pot_settings_dict["Name"]+" ("+self.connector+")"
        self.name = self.pot_settings_dict["Name"].lower()
        self.tcon_setting = self.pot_settings_dict["SSS2 TCON Setting"]
        self.setup_potentometer()
      
    def setup_potentometer(self):        
        self.potentiometer_frame = tk.LabelFrame(self.root, name=self.name+'_frame',text=self.label)
        self.potentiometer_frame.grid(row=self.pot_row,column=self.pot_col,sticky=tk.W,padx=5,pady=5)

        

        self.terminal_A_connect_button =  ttk.Checkbutton(self.potentiometer_frame,
                                                          text="Terminal A Connected",
                                                          name="terminal_A_connect",
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
                                              name='wiper_position_slider',
                                              command = self.set_wiper_voltage)
        self.wiper_position_slider.grid(row=1,column=0,columnspan=1,rowspan=5,sticky="E")
        self.wiper_position_slider.set(self.pot_settings_dict["Wiper Position"])
        tk.Label(self.potentiometer_frame,text="Wiper Position",name="wiper label").grid(row=2,column=1, sticky="S",columnspan=2)
        self.wiper_position_value = ttk.Entry(self.potentiometer_frame,width=10,name='wiper_position_value')
        self.wiper_position_value.grid(row=3,column = 1,sticky="E")
        self.wiper_position_value.bind('<Return>',self.set_wiper_slider)

        self.wiper_position_button = ttk.Button(self.potentiometer_frame,text="Set Position",
                                            command = self.set_wiper_slider,name='wiper_position_button')
        self.wiper_position_button.grid(row=3,column = 2,sticky="W")


       
        self.wiper_connect_button =  ttk.Checkbutton(self.potentiometer_frame, text="Wiper Connected",
                                            command=self.set_terminals,name='wiper_connect_checkbutton')
        self.wiper_connect_button.grid(row=4,column=1,columnspan=2,sticky=tk.NW)
        self.wiper_connect_button.state(['!alternate']) #Clears Check Box
        if self.pot_settings_dict["Wiper Connect"]:
            self.wiper_connect_button.state(['selected']) #checks the Box
        

        self.terminal_B_connect_button =  ttk.Checkbutton(self.potentiometer_frame,
                                                          text="Terminal B Connected",
                                                          name="terminal_B_connect",
                                                          command=self.set_terminals)
        self.terminal_B_connect_button.grid(row=5,column=1,columnspan=2,sticky=tk.SW)
        self.terminal_B_connect_button.state(['!alternate']) #Clears Check Box
        if self.pot_settings_dict["Term. B Connect"]:
            self.terminal_B_connect_button.state(['selected']) 
        
        self.set_terminals()

        self.ecu_app = ecu_application(self.potentiometer_frame,self.pot_settings_dict,row=6,column=0,columnspan=4)
        
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
        return send_serial_command(commandString)
    
    def set_terminals(self):
        self.terminal_A_connect_state = self.terminal_A_connect_button.instate(['selected'])
        self.terminal_B_connect_state = self.terminal_B_connect_button.instate(['selected'])
        self.wiper_connect_state = self.wiper_connect_button.instate(['selected'])
        terminal_setting = self.terminal_B_connect_state + 2*self.wiper_connect_state + 4*self.terminal_A_connect_state
        commandString = "{},{}".format(self.tcon_setting,terminal_setting)
        return send_serial_command(commandString)

class DAC7678(SSS2):
    def __init__(self, parent,sss2_settings, row = 2, col = 0):
        self.root = parent
        self.row=row
        self.col=col
        self.settings_dict = sss2_settings
        self.connector=self.settings_dict["Pin"]
        self.label = self.settings_dict["Name"]+" ("+self.connector+")"
        self.name = self.label.lower()
        self.setting_num = self.settings_dict["SSS2 setting"]
        self.setup_dac_widget()
        
    def setup_dac_widget(self):
         
        self.dac_frame = tk.LabelFrame(self.root, name=self.name,text=self.label)
        self.dac_frame.grid(row=self.row,column=self.col,sticky=tk.W,padx=5,pady=5)
        self.low = float(self.settings_dict["Lowest Voltage"])
        self.high = float(self.settings_dict["Highest Voltage"])

        self.dac_mean_slider = tk.Scale(self.dac_frame,
                                        from_ = self.low*100,
                                        to = self.high*100,
                                        digits = 1, resolution = 1,
                                        orient = tk.HORIZONTAL, length = 200,
                                        sliderlength = 10, showvalue = 0, 
                                        label = "Mean Value",
                                        name = self.name,
                                        command = self.set_dac_voltage)
        self.dac_mean_slider.grid(row=0,column=0,columnspan=1)
        self.dac_mean_position_value = ttk.Entry(self.dac_frame,width=5)
        self.dac_mean_position_value.grid(row=0,column = 1,sticky="SE")
        self.dac_mean_position_value.insert(0,self.dac_mean_slider.get())
        self.dac_mean_position_value.bind('<Return>',self.set_dac_mean_slider)

        self.dac_mean_slider.set(self.settings_dict["Average Voltage"]*100)


        self.wiper_position_button = ttk.Button(self.dac_frame,text="Set Voltage",
                                                width=15,
                                                command = self.set_dac_mean_slider)
        self.wiper_position_button.grid(row=0,column = 2,sticky="SW",columnspan=1)

        self.range_frame = tk.Frame(self.dac_frame)
        self.range_frame.grid(row=1,column=0,columnspan=3)
        self.range_frame.grid_columnconfigure(1,weight=2)
        tk.Label(self.range_frame,text="Low: {} V".format(self.low)).grid(row=0,column=0, sticky="E",columnspan=1)
        tk.Label(self.range_frame,text="High: {} V".format(self.high)).grid(row=0,column=2,sticky="E",columnspan=1)


        self.ecu_app = ecu_application(self.dac_frame,self.settings_dict,row=1,column=0,columnspan=3)
   
   
    def set_dac_voltage(self,event=None):
            
        self.dac_mean_position_value.delete(0,tk.END)
        self.dac_mean_position_value.insert(0,self.dac_mean_slider.get()/100)
        x=float(self.dac_mean_position_value.get())
        if self.setting_num == 49:
            dac_raw_setting = int(4.2646*x - 16.788)
        else:
            slope = 4095/(self.high-self.low)
            dac_raw_setting = int(slope*(x - self.low))
        commandString = "{},{:d}".format(self.setting_num,dac_raw_setting)
        return send_serial_command(commandString)
        
    
    def set_dac_mean_slider(self,event=None):
        entry_value = self.dac_mean_position_value.get()
        #print(entry_value)
        self.dac_mean_position_value['foreground'] = "black"
        try:
            self.dac_mean_slider.set(float(entry_value)*100)
        except Exception as e:
            print(e)
            self.root.bell()
            self.dac_mean_position_value['foreground'] = "red"


class pwm_out(SSS2):
    def __init__(self, parent,sss2_settings, row = 2, col = 0):
        self.root = parent
        self.row=row
        self.col=col
        self.settings_dict = sss2_settings
        self.number=self.settings_dict["Port"]
        self.connector=self.settings_dict["Pin"]
        self.label = self.settings_dict["Name"]+" ("+self.connector+")"
        self.name = self.label.lower()
        self.setting_num = self.settings_dict["SSS2 setting"]
        self.setup_pwm_widget()
        
    def setup_pwm_widget(self):
         
        self.pwm_frame = tk.LabelFrame(self.root, name=self.name,text=self.label)
        self.pwm_frame.grid(row=self.row,column=self.col,sticky=tk.W,padx=5,pady=5)
        
        self.pwm_duty_cycle_slider = tk.Scale(self.pwm_frame,
                                        from_ = 0,
                                        to = 100,
                                        digits = 1, resolution = 0.1,
                                        orient = tk.HORIZONTAL, length = 200,
                                        sliderlength = 10, showvalue = 0, 
                                        label = "Duty Cycle (Hz)",
                                        name = self.name+'_duty_cycle',
                                        command = self.set_pwm_duty_cycle)
        self.pwm_duty_cycle_slider.grid(row=0,column=0)
        self.pwm_duty_cycle_value = ttk.Entry(self.pwm_frame,width=5)
        self.pwm_duty_cycle_value.grid(row=0,column = 1,sticky="SE")
        self.pwm_duty_cycle_slider.set(self.settings_dict["Duty Cycle"])
        self.pwm_duty_cycle_value.insert(0,self.pwm_duty_cycle_slider.get())
        self.pwm_duty_cycle_value.bind('<Return>',self.set_pwm_duty_cycle_slider)


        self.wiper_position_button = ttk.Button(self.pwm_frame,text="Set Duty Cycle",
                                                width=15,
                                            command = self.set_pwm_duty_cycle_slider)
        self.wiper_position_button.grid(row=0,column = 2,sticky="SW",columnspan=1)


        self.pwm_frequency_slider = tk.Scale(self.pwm_frame,
                                        from_ = self.settings_dict["Lowest Frequency"],
                                        to = self.settings_dict["Highest Frequency"],
                                        digits = 1,
                                        resolution = (self.settings_dict["Highest Frequency"] -
                                                      self.settings_dict["Lowest Frequency"])/200,
                                        orient = tk.HORIZONTAL, length = 200,
                                        sliderlength = 10, showvalue = 0, 
                                        label = "Frequency (Hz)",
                                        name = self.name+'_frequency',
                                        command = self.set_pwm_frequency)
        self.pwm_frequency_slider.grid(row=1,column=0)
        self.pwm_frequency_value = ttk.Entry(self.pwm_frame,width=5)
        self.pwm_frequency_value.grid(row=1,column = 1,sticky="SE")
        
        self.pwm_frequency_slider.set(self.settings_dict["Frequency"])
        self.pwm_frequency_value.insert(0,self.pwm_frequency_slider.get())
        self.pwm_frequency_value.bind('<Return>',self.set_pwm_frequency_slider)


        self.frequency_button = ttk.Button(self.pwm_frame,text="Set Frequency",
                                                width=15,
                                            command = self.set_pwm_frequency_slider)
        self.frequency_button.grid(row=1,column = 2,sticky="SW",columnspan=1)
        

        self.ecu_app = ecu_application(self.pwm_frame,self.settings_dict,row=2,column=0,columnspan=3)
   
    def set_pwm_frequency(self,event=None):
        self.pwm_frequency_value.delete(0,tk.END)
        self.pwm_frequency_value.insert(0,self.pwm_frequency_slider.get())
        
        slope = 1
        pwm_raw_setting = int(slope*(float(self.pwm_frequency_value.get())))
        commandString = "{},{}".format(self.setting_num+48,pwm_raw_setting)
        return send_serial_command(commandString)

    def set_pwm_duty_cycle(self,event=None):
             
        self.pwm_duty_cycle_value.delete(0,tk.END)
        self.pwm_duty_cycle_value.insert(0,self.pwm_duty_cycle_slider.get())
        
        slope = 4096/100
        pwm_raw_setting = int(slope*(float(self.pwm_duty_cycle_value.get())))
        commandString = "{},{}".format(self.setting_num,pwm_raw_setting)
        return send_serial_command(commandString)

    def set_pwm_frequency_slider(self,event=None):
        entry_value = self.pwm_frequency_value.get()
        #print(entry_value)
        self.pwm_frequency_value['foreground'] = "black"
        try:
            self.pwm_frequency_slider.set(float(entry_value))
        except Exception as e:
            print(e)
            self.root.bell()
            self.pwm_frequency_value['foreground'] = "red"
    
    def set_pwm_duty_cycle_slider(self,event=None):
        entry_value = self.pwm_duty_cycle_value.get()
        #print(entry_value)
        self.pwm_duty_cycle_value['foreground'] = "black"
        try:
            self.pwm_duty_cycle_slider.set(float(entry_value))
        except Exception as e:
            print(e)
            self.root.bell()
            self.pwm_duty_cycle_value['foreground'] = "red"
            
class ecu_application(SSS2):
    def __init__(self, parent, ecu_settings, row = 2, column = 0,columnspan=3,rowspan=1):
        self.root = parent
        self.row=row
        self.col=column
        self.rowspan=rowspan
        self.colspan=columnspan
        self.settings_dict = ecu_settings
        self.setup_ecu_application()
        
    def setup_ecu_application(self):
        
        self.ecu_frame = tk.LabelFrame(self.root,name='ecu_frame',text="ECU Application")
        self.ecu_frame.grid(row=self.row,column=self.col,columnspan=self.colspan,
                            rowspan=self.rowspan,sticky=tk.E+tk.W)
        self.ecu_frame.grid_columnconfigure(2,weight=2)
        
        tk.Label(self.ecu_frame,text="ECU Pins:").grid(row=0,column=0, sticky=tk.W)
        
        self.ecu_pins = ttk.Entry(self.ecu_frame,width=18,name="ecu pins")
        self.ecu_pins.insert(0,self.settings_dict["ECU Pins"])
        self.ecu_pins.grid(row=0,column=1,sticky=tk.W)
        
        self.ecu_app = tk.Entry(self.ecu_frame,name="ecu application")
        self.ecu_app.insert(tk.END,self.settings_dict["Application"])
        self.ecu_app.grid(row=1,column=0,columnspan=3,sticky=tk.E+tk.W)

        
def send_serial_command(commandString):
        command_bytes = bytes(commandString,'ascii') + b'\n'
        print(command_bytes)
        global ser
        try:
            ser.write(command_bytes)
            return command_bytes    
        except Exception as e:
            print(e)
            return False            
            
if __name__ == '__main__':

    root = tk.Tk()
    mainwindow = SSS2(root,name='sss2')
    root.mainloop()
    try:
        root.destroy() # if mainloop quits, destroy window
    except:
        print("Bye.")
