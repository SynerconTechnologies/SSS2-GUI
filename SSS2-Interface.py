import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
import serial
import serial.tools.list_ports
import os
import threading
import queue
import time
import string
import hashlib
from pprint import pformat
import re

from tkinter.tix import *
from tkinter.constants import *
import tkinter.scrolledtext as tkst

from SSS2_defaults import *


            
class SerialThread(threading.Thread):
    def __init__(self, parent, rx_queue, tx_queue,serial):
        self.root = parent
        threading.Thread.__init__(self)
        self.rx_queue = rx_queue
        self.tx_queue = tx_queue
        self.serial=serial
        
    def run(self):
        time.sleep(1)
        try:
            while True:
            
                if self.tx_queue.qsize():
                    s = self.tx_queue.get_nowait()
                    self.serial.write(bytes(s,'utf-8') + b'\x0A')
                    print('TX: ', end='')
                    print(s)
                if self.serial.inWaiting():
                    lines = self.serial.readlines(self.serial.inWaiting())
                    for line in lines:
                        self.rx_queue.put(line)
                        #print('RX: ', end='')
                        #print(line)
                time.sleep(.003)
        except Exception as e:
            print(e)
            print("Serial Connection Broken. Exiting Thread.")
            self.serial.close()
            

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
       
        self.serial=False
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
        self.populate_combo_box()
        
       

    def find_serial_ports(self):
        comPorts = []
        comPorts.append("Not Available")
        for possibleCOMPort in serial.tools.list_ports.comports():
            comPortstr =  str(possibleCOMPort).split()  
                
            if ('Teensy' in str(possibleCOMPort)):
                comPort = re.sub(r'\W+', '',comPortstr[0])+ " (SSS2)"
            else:
                comPort =  re.sub(r'\W+', '',comPortstr[0])
            comPorts.append(comPort)
        return comPorts
    
    def populate_combo_box(self):
        comPorts = self.find_serial_ports()
        self.port_combo_box['values'] = comPorts[::-1]
        self.port_combo_box.current(0)

        self.after(4000,self.populate_combo_box)
        
    # standard button semantics

    def ok(self, event=None):

        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply() #usually this is in the OK function

        self.cancel()
        
    def cancel(self, event=None):
        
        # put focus back to the parent window
        
        self.parent.focus_set()
        self.destroy()

    #
    # command hooks

    def validate(self):
        if self.port_combo_box.get() == "Not Available":
            messagebox.showerror("SSS2 Serial Connection Error",
                   "SSS2 Connection is not available. Please plug in the SSS2 and be sure the drivers are installed." )
            self.result= None
            
        else:
            try:
                comport=(self.port_combo_box.get().split(" "))[0]
                ser = serial.Serial(comport,baudrate=4000000,timeout=0,
                                    parity=serial.PARITY_ODD,write_timeout=0,
                                    xonxoff=False, rtscts=False, dsrdtr=False)
                self.result = ser
                return True
            except Exception as e:
                print(e)
                messagebox.showerror("SSS2 Serial Connection Error",
                   "The new SSS2 serial connection did not respond properly. The program gives the following error: {}".format(e) )
                self.result= False
        return False
    def apply(self):
        
        self.parent.focus_set()
        self.destroy()

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
        self.filename=os.path.expanduser('~')+'\\SSS2settings.SSS2'
        self.file_authenticated = False
        self.file_OK_received = tk.BooleanVar(name='file_OK_received')
        self.file_OK_received.set(False)
        self.init_gui()
        
 
    def init_gui(self):
        """Builds GUI."""
        
        self.tx_queue = queue.Queue()
        self.rx_queue = queue.Queue()
       

        # Button to do something on the right
        self.ignition_key_button =  ttk.Checkbutton(self,name='ignition_key_switch',
                                            text="Ignition Key Switch",
                                            command=self.send_ignition_key_command)
        self.ignition_key_button.grid(row=0,column=1)
        self.ignition_key_button.state(['!alternate']) #Clears Check Box
        
        
        ttk.Label(self, text='USB/Serial Monitor:').grid(row=0,column=1,sticky=tk.E)
        self.serial_rx_entry = tk.Entry(self,width=60,name='serial_monitor')
        self.serial_rx_entry.grid(row=0,column=2,sticky=tk.W+tk.E)
        
        self.tabs = ttk.Notebook(self, name='tabs')
        self.tabs.grid(row=1,column=0,columnspan=3,sticky=tk.W)
        
        

        
        # create each Notebook tab in a Frame
        #Create a Settings Tab to amake the adjustments for sensors
        self.profile_tab = tk.Frame(self.tabs, name='profile_tab')
        self.tabs.add(self.profile_tab, text="ECU Profile Settings") # add tab to Notebook

        #Create a Potentiometers Tab to amake the adjustments for sensors
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

        self.tabs.enable_traversal()
        
          
        self.root.option_add('*tearOff', 'FALSE')
        self.menubar = tk.Menu(self.root,name='main_menus')
 
        self.menu_file = tk.Menu(self.menubar)
        self.menu_connection = tk.Menu(self.menubar)

        self.menu_file.add_command(label='Open...', command=self.open_settings_file, accelerator="Ctrl+O")
        self.menu_file.add_command(label='Save', command=self.save_settings_file, accelerator="Ctrl+S")
        self.menu_file.add_command(label='Save As...', command=self.saveas_settings_file, accelerator="Ctrl+A")
        self.menu_file.add_command(label='Save Serial Log', command=self.save_log_file, accelerator="Ctrl+L")
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Refresh', command=self.init_tabs, accelerator="Ctrl+R")
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Exit', command=self.root.quit, accelerator="Ctrl+Q")
        self.menu_connection.add_command(label='Select COM Port',
                                         command=self.connect_to_serial)

        self.menubar.add_cascade(menu=self.menu_file, label='File')
        self.menubar.add_cascade(menu=self.menu_connection, label='Connection')

        self.bind_all("<Control-o>",self.open_settings_file)
        self.bind_all("<Control-s>",self.save_settings_file)
        self.bind_all("<Control-a>",self.saveas_settings_file)
        self.bind_all("<Control-r>",self.init_tabs)
        self.bind_all("<Control-q>",self.on_quit)
        self.bind_all("<Control-k>",self.send_ignition_key_command)
        self.bind_all("<Control-l>",self.save_log_file)
        
        self.root.config(menu=self.menubar)

        self.serial_connected = False
        self.serial_rx_byte_list = []
        self.received_can0_messages=[]
        self.received_can1_messages=[]
        self.received_can2_messages=[]
        self.received_j1708_messages=[]

        self.serial_interface()
        self.connect_to_serial()
        self.process_serial()
        
    def init_tabs(self,event=None):
        for child in self.settings_tab.winfo_children():
            child.destroy()        
        for child in self.voltage_out_tab.winfo_children():
            child.destroy()
        for child in self.truck_networks_tab.winfo_children():
            child.destroy()

        self.send_stream_A21()
        self.send_stream_can0()
        self.send_stream_can1()

        self.potentiometer_settings() #put this after the serial connections

        self.voltage_out_settings()

        self.vehicle_networks_settings()

        self.profile_settings()

        self.display_file_shas()

        self.update_sha()

        self.tabs.select(self.connections)
        self.tabs.select(self.truck_networks_tab)
        self.tabs.select(self.voltage_out_tab)
        self.tabs.select(self.settings_tab)
        self.tabs.select(self.profile_tab)
        
         
    def display_file_shas(self):
        self.file_box = tk.Frame(self)
        self.file_box.grid(row=2,column=1,rowspan=3)

        tk.Label(self.file_box,text="Settings File:").grid(row=0,column=0,sticky=tk.E)
        self.file_status_string = tk.StringVar(name='file_status_string')
        self.file_status_string.set("Default Settings Loaded")
        self.file_status_label = tk.Label(self.file_box, textvariable=self.file_status_string,name="file_status_label")
        self.file_status_label.grid(row=0,column=1,sticky=tk.W)

        tk.Label(self.file_box,text="Current SHA-256 Digest:").grid(row=1,column=0,sticky=tk.E)
        self.settings_sha_string = tk.StringVar(name='settings-SHA')
        self.settings_sha_string.set(self.get_settings_hash())
        self.settings_sha_label = tk.Label(self.file_box, textvariable=self.settings_sha_string,name="settings_sha_label")
        self.settings_sha_label.grid(row=1,column=1,sticky=tk.W,columnspan=3)

        tk.Label(self.file_box,text="Saved File SHA-256 Digest:").grid(row=2,column=0,sticky=tk.E)
        self.file_sha_string = tk.StringVar(name='file-SHA')
        self.file_sha_string.set(self.settings_dict["Original File SHA"])
        self.file_sha_label = tk.Label(self.file_box, textvariable=self.file_sha_string,name="file_sha_label")
        self.file_sha_label.grid(row=2,column=1,sticky=tk.W,columnspan=3)

        
        
        
    def open_settings_file(self,event=None):
          
        types = [('Smart Sensor Simulator 2 Settings Files', '*.SSS2'),('All Files', '*')]
        idir = os.path.expanduser('~')
        ifile = self.filename
        title='SSS2 Settings File'
        self.filename = filedialog.askopenfilename(filetypes=types,
                                                     initialdir=idir,
                                                     initialfile=ifile,
                                                     title=title,
                                                     defaultextension=".SSS2")
        with open(self.filename,'r') as infile:
            self.settings_dict=json.load(infile)

        self.file_status_string.set("Opened "+self.filename)
        print("Opened "+self.filename)

        

        digest_from_file=self.settings_dict["SHA256 Digest"]
        print("digest_from_file: ",end='')
        print(digest_from_file)

        self.load_settings_file()
        ok_to_open = False
        
        newhash=self.get_settings_hash()
        print("newhash:          ",end='')
        print(newhash)
        if newhash==digest_from_file:
            print("Hash digests match.")
            sss2_id = self.settings_dict["SSS2 Product Code"]
            if not sss2_id == "UNIVERSAL":
                try:
                    if self.serial.isOpen():
                        
                        command_string = "OK,"+sss2_id
                        self.tx_queue.put_nowait(command_string)
                        self.wait_variable(self.file_OK_received)       
                        print("self.file_OK_received: ",end='')
                        self.file_OK_received.set(False)
                        if not self.file_authenticated:
                            self.settings_dict = get_default_settings()
                            messagebox.showwarning("Incompatible SSS2",
                                "The Unique ID for the SSS2 does not match the file. Files are save for specific SSS2 units only and cannot be transfered from one to another. Please enter or get the correct Unique ID")
                            self.tabs.select(self.profile_tab)
                            self.sss2_product_code.focus()
                            self.sss2_product_code['bg']='yellow'
                        else:
                            ok_to_open = True    
                    else:
                        messagebox.showerror("SSS2 Needed to Open File",
                           "Please connect the Smart Sensor Simulator 2 with USB to open a file. User saved files are spcific to each SSS2 unit.")
                        self.connect_to_serial()


                except Exception as e:
                    print(e)
                    messagebox.showerror("Connect SSS2",
                           "Please connect to the Smart Sensor Simulator 2 unit with serial number {} to open a file. Be sure the SSS2 product code under the\n USB/Serial Interface tab is correct. The current code that is entered is {}.".format(self.settings_dict["Serial Number"],self.settings_dict["SSS2 Product Code"]) )
                    self.connect_to_serial()
                  
        else:
            print("Hash values different, Reloading defaults.")
            self.settings_dict = get_default_settings()
            messagebox.showerror("File Integrity Error",
                    "The hash value from the file\n {}\n does not match the new calculated hash.\n The file may have been altered. \nReloading defaults.".format(self.filename) )
            self.file_status_string.set("Error Opening "+self.filename)
        if ok_to_open:
            self.load_settings_file()
        else:
            self.settings_dict = get_default_settings()    
        self.init_tabs()
        
        
    
    def saveas_settings_file(self,event=None):
        types = [('Smart Sensor Simulator 2 Settings Files', '*.SSS2')]
        idir = os.path.expanduser('~')
        ifile = self.filename
        title='SSS2 Settings File'
        self.filename = filedialog.asksaveasfilename( filetypes=types,
                                           initialdir=idir+"Documents",
                                           initialfile=ifile,
                                           title=title,
                                           defaultextension=".SSS2")
        self.save_settings_file()

    def save_settings_file(self,event=None):
        ok_to_save = False
        sss2_id = self.sss2_product_code_text.get()
        ###Take out this Conditional for production
        if not sss2_id == "UNIVERSAL":
            #print(self.serial)
            if self.serial:
                if self.serial is not None:
                    command_string = "OK,"+sss2_id
                    self.tx_queue.put_nowait(command_string)
                    self.wait_variable(self.file_OK_received)       
                    self.file_OK_received.set(False)
                    if self.file_authenticated: 
                        ok_to_save = True 
        else:
            ok_to_save = True

        if ok_to_save:
            self.update_dict()
            self.settings_dict["SHA256 Digest"]=self.get_settings_hash()
            

            ###Take out this Conditional for production
            if sss2_id == "UNIVERSAL":
                self.settings_dict["Original File SHA"]=self.settings_dict["SHA256 Digest"]
            
            with open(self.filename,'w') as outfile:
                json.dump(self.settings_dict,outfile,indent=4)
            self.file_status_string.set("Saved "+self.filename)
            print("Saved "+self.filename) 
        else:
            self.file_status_string.set("File not saved.")
            print("File not saved.") 
            messagebox.showerror("Incompatible SSS2 for Saving",
                            "The unique ID entered for the SSS2 does not match the unit. Please press the Get ID button for the SSS2 Unique ID to populate the form.")
            self.tabs.select(self.profile_tab)
            self.sss2_product_code.focus()
            self.sss2_product_code['bg']='yellow'
        
    def save_log_file(self,event=None):
        with open(self.filename+".log",'w') as log_file:
            for byte_entry in self.serial_rx_byte_list:
                log_file.write(byte_entry.decode('ascii',"ignore"))
                               
    def get_settings_hash(self):
        
        digest_from_file=self.settings_dict["Original File SHA"]
        self.settings_dict.pop("SHA256 Digest",None)
        self.settings_dict.pop("Original File SHA",None)
        temp_settings_dict = pformat(self.settings_dict)
        new_hash = str(hashlib.sha256(bytes(temp_settings_dict,'utf-8')).hexdigest())
        self.settings_dict["SHA256 Digest"] = new_hash
        self.settings_dict["Original File SHA"] = digest_from_file
        return new_hash
    
    def update_sha(self):
        self.update_dict()
        self.file_sha_string.set(self.settings_dict["Original File SHA"])
        self.settings_sha_string.set(self.get_settings_hash())
        self.after(500,self.update_sha)

    def profile_settings(self):
        self.ecu_frame = tk.LabelFrame(self.profile_tab, name="ecu_frame",
                                                  text="Electronic Control Unit (ECU) Settings")
        self.ecu_frame.grid(row=0,column=0,sticky=tk.E+tk.W,columnspan=1)
        #User Changable values
        tk.Label(self.ecu_frame,text="ECU Year:").grid(row=0,column=0,sticky=tk.W)
        self.ecu_year_text = tk.StringVar(value = self.settings_dict["ECU Year"])
        self.ecu_year = tk.Entry(self.ecu_frame,textvariable= self.ecu_year_text, width=5)
        self.ecu_year.grid(row=0,column=1,sticky=tk.W,padx=5,pady=8)

        tk.Label(self.ecu_frame,text="ECU Make:").grid(row=0,column=3,sticky=tk.E)
        self.ecu_make_text = tk.StringVar(value = self.settings_dict["ECU Make"])
        self.ecu_make = tk.Entry(self.ecu_frame,textvariable= self.ecu_make_text, width=16)
        self.ecu_make.grid(row=0,column=4,sticky=tk.W,padx=5,pady=8)

        tk.Label(self.ecu_frame,text="ECU Model:").grid(row=0,column=5,sticky=tk.E)
        self.ecu_model_text = tk.StringVar(value = self.settings_dict["ECU Model"])
        self.ecu_model = tk.Entry(self.ecu_frame,textvariable= self.ecu_model_text, width=16)
        self.ecu_model.grid(row=0,column=6,sticky=tk.W,padx=5,pady=8)

        tk.Label(self.ecu_frame,text="ECU Software Version:").grid(row=2,column=0,sticky=tk.W,columnspan=2)
        self.sss_ecu_id_text = tk.StringVar(value = self.settings_dict["ECU Software Version"])
        self.sss_ecu_id = tk.Entry(self.ecu_frame, textvariable= self.sss_ecu_id_text, width=64)
        self.sss_ecu_id.grid(row=2,column=2,sticky=tk.W,padx=5,pady=8,columnspan=6)
        #tk.Button(self.ecu_frame,text="Get SW",command=self.get_ecu_software_id).grid(row=2,column=8,sticky=tk.W,padx=5)

        tk.Label(self.ecu_frame,text="Engine Serial Number:").grid(row=1,column=0,sticky=tk.W,columnspan=2)
        self.engine_serial_text = tk.StringVar(value = self.settings_dict["Engine Serial Number"])
        self.engine_serial = tk.Entry(self.ecu_frame, textvariable= self.engine_serial_text, width=64)
        self.engine_serial.grid(row=1,column=2,sticky=tk.W,padx=5,pady=8,columnspan=6)
        
        tk.Label(self.ecu_frame,text="Veh. Year:").grid(row=3,column=0,sticky=tk.W)
        self.vehicle_year_text = tk.StringVar(value = self.settings_dict["Vehicle Year"])
        self.vehicle_year = tk.Entry(self.ecu_frame,textvariable= self.vehicle_year_text, width=5)
        self.vehicle_year.grid(row=3,column=1,sticky=tk.W,padx=5,pady=8)

        tk.Label(self.ecu_frame,text="Vehicle Make:").grid(row=3,column=3,sticky=tk.E)
        self.vehicle_make_text = tk.StringVar(value = self.settings_dict["Vehicle Make"])
        self.vehicle_make = tk.Entry(self.ecu_frame,textvariable= self.vehicle_make_text, width=16)
        self.vehicle_make.grid(row=3,column=4,sticky=tk.W,padx=5,pady=8)

        tk.Label(self.ecu_frame,text="Vehicle Model:").grid(row=3,column=5,sticky=tk.E)
        self.vehicle_model_text = tk.StringVar(value = self.settings_dict["Vehicle Model"])
        self.vehicle_model = tk.Entry(self.ecu_frame,textvariable= self.vehicle_model_text, width=16)
        self.vehicle_model.grid(row=3,column=6,sticky=tk.W,padx=5,pady=8)

        tk.Label(self.ecu_frame,text="Vehicle ID (VIN):").grid(row=4,column=0,sticky=tk.W,columnspan=2)
        self.vehicle_vin_text = tk.StringVar(value = self.settings_dict["Vehicle VIN"])
        self.vehicle_vin = tk.Entry(self.ecu_frame, textvariable= self.engine_serial_text, width=64)
        self.vehicle_vin.grid(row=4,column=2,sticky=tk.W,padx=5,pady=8,columnspan=6)

        tk.Label(self.ecu_frame,text="ECU Component ID:").grid(row=5,column=0,sticky=tk.W,columnspan=2)
        self.ecu_component_id_text = tk.StringVar(value = self.settings_dict["ECU Component ID"])
        self.ecu_component_id = tk.Entry(self.ecu_frame, textvariable= self.ecu_component_id_text, width=64)
        self.ecu_component_id.grid(row=5,column=2,sticky=tk.W,padx=5,pady=8,columnspan=6)
        #tk.Button(self.ecu_frame,text="Get ID",command=self.get_ecu_software_id).grid(row=5,column=8,sticky=tk.W,padx=5)

        tk.Label(self.ecu_frame,text="ECU Configuration:").grid(row=6,column=0,sticky=tk.W,columnspan=2)
        self.ecu_configuration_text = tk.StringVar(value = self.settings_dict["Engine Configuration"])
        self.ecu_configuration = tk.Entry(self.ecu_frame, textvariable= self.ecu_configuration_text, width=64)
        self.ecu_configuration.grid(row=6,column=2,sticky=tk.W,padx=5,pady=8,columnspan=6)
        
        
        self.sss2_frame = tk.LabelFrame(self.profile_tab, name="sss2_frame",
                                                  text="Smart Sensor Simulator 2 (SSS2) Settings")
        self.sss2_frame.grid(row=1,column=0,sticky=tk.E+tk.W,columnspan=1)

        tk.Label(self.sss2_frame,text="SSS2 Component ID:").grid(row=0,column=0,sticky=tk.W)
        self.sss_component_id_text = tk.StringVar(value = self.settings_dict["Component ID"])
        self.sss2_serial_number = tk.Entry(self.sss2_frame, name="sss2_serial",textvariable=self.sss_component_id_text,width=65)
        self.sss2_serial_number.grid(row=0,column=1,sticky=tk.W,padx=5,pady=8)
        #self.sss2_serial_number.insert(0,self.settings_dict["Component ID"])
        tk.Button(self.sss2_frame,text="Get ID",command=self.get_sss2_component_id).grid(row=0,column=7,sticky=tk.W)
        tk.Button(self.sss2_frame,text="Set ID",command=self.set_sss2_component_id).grid(row=0,column=8,sticky=tk.W,padx=5)


        tk.Label(self.sss2_frame,text="SSS2 Unique ID:").grid(row=1,column=0,sticky=tk.W)
        self.sss2_product_code_text = tk.StringVar(value = self.settings_dict["SSS2 Product Code"])
        self.sss2_product_code = tk.Entry(self.sss2_frame,textvariable= self.sss2_product_code_text,width=65)
        self.sss2_product_code.grid(row=1,column=1,sticky=tk.W,padx=5,pady=8)
        tk.Button(self.sss2_frame,text="Get ID",command=self.get_sss2_unique_id).grid(row=1,column=7,sticky=tk.W)


        tk.Label(self.sss2_frame,text="SSS2 Software ID:").grid(row=2,column=0,sticky=tk.W)
        self.sss_software_id_text = tk.StringVar(value = self.settings_dict["Software ID"])
        self.sss_software_id = tk.Entry(self.sss2_frame, textvariable= self.sss_software_id_text, width=65)
        self.sss_software_id.grid(row=2,column=1,sticky=tk.W,padx=5,pady=8,columnspan=6)
        tk.Button(self.sss2_frame,text="Get ID",command=self.get_sss2_software_id).grid(row=2,column=7,sticky=tk.W)

        self.file_frame = tk.LabelFrame(self.profile_tab, name="file_frame",
                                                  text="Current Settings Information")
        self.file_frame.grid(row=1,column=1,sticky=tk.N+tk.E+tk.W,columnspan=1)

        
        tk.Label(self.file_frame,text="Settings File:").grid(row=0,column=0,sticky=tk.E)
        self.file_status_string = tk.StringVar(name='file_status_string')
        self.file_status_string.set("Default Settings Loaded")
        self.file_status_label = tk.Label(self.file_frame, textvariable=self.file_status_string,name="file_status_label")
        self.file_status_label.grid(row=0,column=1,sticky=tk.W)
        tk.Button(self.file_frame,text="Save",command=self.save_settings_file).grid(row=0,column=7,sticky=tk.W,padx=5)

        tk.Label(self.file_frame,text="Current SHA-256 Digest:").grid(row=1,column=0,sticky=tk.E)
        self.settings_sha_string = tk.StringVar(name='settings-SHA')
        self.settings_sha_string.set(self.get_settings_hash())
        self.settings_sha_label = tk.Label(self.file_frame, textvariable=self.settings_sha_string,name="settings_sha_label")
        self.settings_sha_label.grid(row=1,column=1,sticky=tk.W,columnspan=3)

        self.user_frame = tk.LabelFrame(self.profile_tab, name="user_frame",
                                                  text="User Information")
        self.user_frame.grid(row=0,column=1,sticky=tk.N+tk.E+tk.W,columnspan=1)

        tk.Label(self.user_frame,text="User Name:").grid(row=0,column=0,sticky=tk.W)
        self.user_name = tk.Entry(self.user_frame, name="user_name",width=68)
        self.user_name.grid(row=0,column=1,sticky=tk.W,padx=5,pady=8)
        self.user_name.insert(0,self.settings_dict["Programmed By"])
       

    def get_ecu_software_id(self):
        pass

    def get_sss2_unique_id(self):
        commandString = "ID,"
        
        self.tx_queue.put_nowait(commandString)
        
    def get_sss2_software_id(self):
        commandString = "SOFT,"
        self.tx_queue.put_nowait(commandString)

    def get_sss2_component_id(self):
        commandString = "CI,"
        self.tx_queue.put_nowait(commandString)

    def set_sss2_component_id(self):
        commandString = "CI,SYNER*SSS2-R3*{}*UNIVERSAL".format(self.sss2_serial_number.get())
        self.tx_queue.put_nowait(commandString)
       
    def load_settings_file(self):
        self.sss2_product_code.delete(0,tk.END)
        self.sss2_product_code.insert(0,self.settings_dict["SSS2 Product Code"])
        self.sss2_serial_number.delete(0,tk.END)
        self.sss2_serial_number.insert(0,self.settings_dict["Serial Number"])
        self.ecu_year.delete(0,tk.END)
        self.ecu_year.insert(0,self.settings_dict["ECU Year"])
     
    def update_dict(self):
        for bank_key in self.pot_bank.keys():
            group=self.settings_dict["Potentiometers"][bank_key]
            
            if group["Terminal A Connection"]:
                group["Terminal A Connection"] = self.pot_bank[bank_key].bank_button.instate(['selected'])
            for pair_key in self.pot_bank[bank_key].pot_pairs.keys():
                pair=group["Pairs"][pair_key]
                if self.pot_bank[bank_key].pot_pairs[pair_key].twelve_volt_switch is not None:
                    if self.pot_bank[bank_key].pot_pairs[pair_key].twelve_volt_switch.instate(['selected']):
                        pair["Terminal A Voltage"] = "+12V"
                    else:
                        pair["Terminal A Voltage"] = "+5V"
                for pot_key in self.pot_bank[bank_key].pot_pairs[pair_key].pots.keys():
                    pot=pair["Pots"][pot_key]
                    pot_object = self.pot_bank[bank_key].pot_pairs[pair_key].pots[pot_key]
                    pot["Term. A Connect"] =    pot_object.terminal_A_connect_button.instate(['selected']) 
                    pot["Term. B Connect"] =    pot_object.terminal_B_connect_button.instate(['selected']) 
                    pot["Wiper Connect"]   =    pot_object.wiper_connect_button.instate(['selected']) 
                    pot["Wiper Position"] = int(pot_object.wiper_position_slider.get())
                    pot["ECU Pins"] =           pot_object.ecu_app.ecu_pins.get()
                    pot["Application"] =        pot_object.ecu_app.ecu_app.get()

        for dac_key in self.dac_objects.keys():
            dac_dict=self.settings_dict["DACs"][dac_key]
            dac_dict["Average Voltage"] = self.dac_objects[dac_key].dac_mean_slider.get()
            dac_dict["ECU Pins"] =        self.dac_objects[dac_key].ecu_app.ecu_pins.get()
            dac_dict["Application"] =     self.dac_objects[dac_key].ecu_app.ecu_app.get()

        for pwm_key in self.pwm_objects.keys():
            pwm_dict=self.settings_dict["PWMs"][pwm_key]
            pwm_dict["Duty Cycle"] = self.pwm_objects[pwm_key].pwm_duty_cycle_slider.get()
            pwm_dict["Frequency"] = self.pwm_objects[pwm_key].pwm_frequency_slider.get()
            pwm_dict["ECU Pins"] =        self.pwm_objects[pwm_key].ecu_app.ecu_pins.get()
            pwm_dict["Application"] =     self.pwm_objects[pwm_key].ecu_app.ecu_app.get()

        hv_dict=self.settings_dict["HVAdjOut"]
        hv_dict["Average Voltage"] = self.hvadjout.dac_mean_slider.get()
        hv_dict["ECU Pins"] =        self.hvadjout.ecu_app.ecu_pins.get()
        hv_dict["Application"] =     self.hvadjout.ecu_app.ecu_app.get()

        s=self.settings_dict["Switches"]        
        s["Port 10 or 19"]["State"]=self.vout2a_switch.switch_buttonA.instate(['selected'])
        s["Port 15 or 18"]["State"]=self.vout2b_switch.switch_buttonA.instate(['selected'])
        s["CAN1 or J1708"]["State"]=self.j1708_switch.switch_buttonA.instate(['selected'])
        s["PWMs or CAN2"]["State"]=self.pwm12_switch.switch_buttonA.instate(['selected'])
        s["CAN0"]["State"]=self.can0_term.switch_button.instate(['selected'])
        s["CAN1"]["State"]=self.can1_term.switch_button.instate(['selected'])
        s["CAN2"]["State"]=self.can2_term.switch_button.instate(['selected'])
        s["LIN Master Pullup Resistor"]["State"]=self.lin_to_master.switch_button.instate(['selected'])
        s["12V Out 2"]["State"]=self.twelve2_switch.switch_button.instate(['selected'])
        s["12V Out 1"]["State"]=self.pwm3_switch.switch_buttonB.instate(['selected'])
        s["Ground Out 1"]["State"]=self.pwm4_switch.switch_buttonB.instate(['selected'])
        s["Ground Out 2"]["State"]=self.ground2_switch.switch_button.instate(['selected'])
        s["LIN to SHLD"]["State"]=self.lin_to_shield_switch.switch_button.instate(['selected'])
        s["LIN to Port 16"]["State"]=self.lin_to_port_16.switch_button.instate(['selected'])
        s["PWM1 Connect"]["State"]=self.pwm1_switch.switch_button.instate(['selected'])
        s["PWM2 Connect"]["State"]=self.pwm2_switch.switch_button.instate(['selected'])
        s["PWM3 or 12V"]["State"]=self.pwm3_switch.switch_buttonA.instate(['selected'])
        s["PWM4 or Ground"]["State"]=self.pwm4_switch.switch_buttonA.instate(['selected'])

        self.settings_dict["SSS2 Product Code"] = self.sss2_product_code.get()
        self.settings_dict["Serial Number"] = self.sss2_serial_number.get()  
        self.settings_dict["ECU Year"] = self.ecu_year.get()
        
    def get_all_children(self,tree, item=""):
        children = tree.get_children(item)
        for child in children:
            children += self.get_all_children(tree, child)
        return children
    def send_transmit_can(self):
        commandString = "STARTCAN,"
        for tree_item in self.get_all_children(self.can_tree):
            print(tree_item)
            self.can_tree.set(tree_item,"Send","Yes")
            
        self.tx_queue.put_nowait(commandString)
        
    def send_stop_can(self):
        commandString = "STOPCAN,"
        for tree_item in self.get_all_children(self.can_tree):
            self.can_tree.set(tree_item,"Send","No")
            self.can_tree.selection_set(tree_item)
        self.tx_queue.put_nowait(commandString)         

    def send_clear_can(self):
        for tree_item in self.can_tree.get_children():
            self.can_tree.delete(tree_item)   
        self.tx_queue.put_nowait("CLEARCAN,")         

    def send_reload_can(self):
        msg_index=0
        for message_string in self.settings_dict["CAN"]["Preprogrammed"]:
            self.load_can_frame(message_string,msgKey)
            time.sleep(0.002)
            msg_index+=1
        self.tx_queue.put_nowait("RELOAD,") 
        
    def vehicle_networks_settings(self):

        self.truck_networks_tab.grid_rowconfigure(5,weight=2) #Expands blank space under radio buttons.


        ttk.Button(self.truck_networks_tab,
                                    text="Transmit all CAN messages", width = 35,
                                    command=self.send_transmit_can).grid(row=1,
                                                                         column=1,
                                                                         sticky="W",
                                                                         pady=5,padx=5)
        
        ttk.Button(self.truck_networks_tab, width = 35,
                                    text="Stop Sending all CAN messages",
                                    command=self.send_stop_can).grid(row=2,
                                                                     column=1,
                                                                     sticky="W",
                                                                     pady=5,padx=5)
##        ttk.Button(self.truck_networks_tab, width = 35,
##                                    text="Clear all CAN messages",
##                                    command=self.send_clear_can).grid(row=3,
##                                                                     column=1,
##                                                                     sticky="W",
##                                                                     pady=5,padx=5)
##        ttk.Button(self.truck_networks_tab, width = 35,
##                                    text="Reload default CAN messages",
##                                    command=self.send_reload_can).grid(row=4,
##                                                                     column=1,
##                                                                     sticky="W",
##                                                                     pady=5,padx=5)
        

        self.can_edit_frame = tk.LabelFrame(self.truck_networks_tab, name="edit_can",text="CAN Message Editor")
        self.can_edit_frame.grid(row=5,column=1,sticky="WE",columnspan=1,rowspan=1)
        self.truck_networks_tab.grid_columnconfigure(6,weight=2) #Expands blank space 

        tk.Label(self.can_edit_frame,text="Description:").grid(row=0,column=0,sticky="E")
        self.can_name_value = tk.StringVar()
        self.can_name = ttk.Entry(self.can_edit_frame,textvariable=self.can_name_value,width=65)
        self.can_name.grid(row=0,column=1,sticky="W",columnspan=6,pady=5)

        tk.Label(self.can_edit_frame,text="Thread:").grid(row=1,column=0,sticky="E")
        self.can_thread_value=tk.StringVar()
        self.can_thread = ttk.Label(self.can_edit_frame,textvariable=self.can_thread_value,width=10)
        self.can_thread.grid(row=1,column=1,sticky="W",pady=5,columnspan=1)

        tk.Label(self.can_edit_frame,text="Sequence Count:").grid(row=1,column=2,sticky="E")
        self.can_count_value=tk.StringVar(value="1")
        self.can_count = ttk.Label(self.can_edit_frame,textvariable=self.can_count_value,width=10)
        self.can_count.grid(row=1,column=3,sticky="W",pady=5,columnspan=1)

        tk.Label(self.can_edit_frame,text="Sequence Index:").grid(row=1,column=4,sticky="E")
        self.can_sub_value=tk.StringVar(value = "0")
        self.can_sub = ttk.Entry(self.can_edit_frame,textvariable=self.can_sub_value,width=10)
        self.can_sub.grid(row=1,column=5,sticky="W",pady=5,columnspan=1)

        
        tk.Label(self.can_edit_frame,text="Hex CAN ID:").grid(row=2,column=0,sticky="E")
        self.can_id_value=tk.StringVar()
        self.can_id = ttk.Entry(self.can_edit_frame,textvariable=self.can_id_value,width=12)
        self.can_id.grid(row=2,column=1,sticky="W",pady=5,columnspan=2)

        tk.Label(self.can_edit_frame,text="DLC:").grid(row=2,column=2,sticky="E")
        self.can_dlc_value=tk.StringVar(value="8")
        combobox_values = ["1","2","3","4","5","6","7","8"]
        self.can_dlc = ttk.Combobox(self.can_edit_frame,textvariable=self.can_dlc_value,width=1,values=combobox_values)
        self.can_dlc.grid(row=2,column=3,sticky="W",pady=5,columnspan=1)

        
        self.can_ext_id_state = tk.IntVar(value=1)
        self.can_ext_id = ttk.Checkbutton(self.can_edit_frame,text="Use Extended (29-bit) ID",variable=self.can_ext_id_state)
        self.can_ext_id.grid(row=2,column=4,sticky="W",padx=10,columnspan=3)
        
        tk.Label(self.can_edit_frame,text="Channel:").grid(row=3,column=0,sticky="E")

        self.can_radio_frame = tk.Frame(self.can_edit_frame)
        self.can_radio_frame.grid(row=3,column=1,sticky="W",columnspan=2,pady=5)
        self.can_channel_value = tk.StringVar(value="0")
        self.can_channel_0 = ttk.Radiobutton(self.can_radio_frame,value="0",text="J1939",variable=self.can_channel_value)
        self.can_channel_0.grid(row=0,column=0,sticky="E")
        self.can_channel_0 = ttk.Radiobutton(self.can_radio_frame,value="1",text="CAN2",variable=self.can_channel_value)
        self.can_channel_0.grid(row=0,column=1,sticky="W")
        
        self.can_send_state = tk.IntVar(value=1)
        self.can_send = ttk.Checkbutton(self.can_edit_frame,
                                        text="Enable Transmission (Send)",
                                        variable=self.can_send_state,
                                        command=self.send_single_frame)
        self.can_send.grid(row=3,column=4,sticky="W",padx=10,columnspan=3)
        
        tk.Label(self.can_edit_frame,text="Period (msec):").grid(row=4,column=0,sticky="E")
        self.can_period_value = tk.StringVar(value="100")
        self.can_period = ttk.Entry(self.can_edit_frame,textvariable=self.can_period_value,width=10)
        self.can_period.grid(row=4,column=1,sticky="W",pady=5)

        tk.Label(self.can_edit_frame,text="  Restart (msec):").grid(row=4,column=2,sticky="E")
        self.can_restart_value = tk.StringVar(value="0")
        self.can_restart = ttk.Entry(self.can_edit_frame,textvariable=self.can_restart_value,width=10)
        self.can_restart.grid(row=4,column=3,sticky="W",pady=5)

        tk.Label(self.can_edit_frame,text="Total to Send:").grid(row=4,column=4,sticky="E")
        self.can_total_value = tk.StringVar(value="0")
        self.can_total = ttk.Entry(self.can_edit_frame,textvariable=self.can_total_value,width=10)
        self.can_total.grid(row=4,column=5,sticky="W")

        self.can_data_frame = tk.Frame(self.can_edit_frame)
        self.can_byte_value=[]
        self.can_byte=[]
        for byteLabel in range(8):
            tk.Label(self.can_data_frame,text=" B{}:".format(byteLabel+1)).grid(row=0,column=2*byteLabel)
            self.can_byte_value.append(tk.StringVar(value="00"))
            self.can_byte.append(ttk.Entry(self.can_data_frame,textvariable=self.can_byte_value[byteLabel],width=3))
            self.can_byte[byteLabel].grid(row=0,column=2*byteLabel+1,pady=5)
            self.can_byte[-1].bind('<Return>',self.modify_can_message)
            self.can_byte[-1].bind('<Tab>',self.modify_can_message)
        self.can_data_frame.grid(row=5,column=1,columnspan=6,sticky="W")
        tk.Label(self.can_edit_frame,text="Data Bytes (Hex):").grid(row=5,column=0,sticky="W")

        self.modify_can_button = ttk.Button(self.can_edit_frame, width = 35,
                                    text="Modify Selected Message",
                                    command=self.modify_can_message)
        self.modify_can_button.grid(row=6,columnspan=3,column=0,sticky="W",
                                                                     pady=5,padx=5)
        ttk.Button(self.can_edit_frame, width = 35,
                                    text="Create New CAN Message",
                                    command=self.create_new_message).grid(row=6,columnspan=3,
                                                                     column=3,
                                                                     sticky="E",
                                                                     pady=5,padx=5)

        self.send_can_button = ttk.Button(self.can_edit_frame, width = 35,
                                    text="Send Selected Message",
                                    command=self.send_single_frame)
        self.send_can_button.grid(row=7,columnspan=3,column=0,sticky="W",pady=5,padx=5)

        self.delete_can_button = ttk.Button(self.can_edit_frame, width = 35,
                                    text="Delete Selected Message",
                                    command=self.delete_can_message)
        self.delete_can_button.grid(row=7,columnspan=3,column=3,sticky="E",pady=5,padx=5)

        self.add_sequence_button = ttk.Button(self.can_edit_frame, width = 35,
                                    text="Add Sequential Message",
                                    command=self.add_sequential_message)
        self.add_sequence_button.grid(row=8,columnspan=3,column=0,sticky="W",pady=5,padx=5)

    
        self.can0_frame = tk.LabelFrame(self.truck_networks_tab, name="can0 Messages",text="CAN Messages to Transmit")
        ttk.Sizegrip(self.can0_frame)
                                                  
        self.can0_frame.grid(row=0,column=0,sticky="NW",columnspan=1,rowspan=7)

        colWidths = [55,55,55,55,55,55,55,55,30,75,24,24,24,24,24,24,24,24,24]
        self.colNames = ["Thread","Count","Index","Send","Channel","Period","Restart","Total","Ext","CAN HEX ID","DLC","B1","B2","B3","B4","B5","B6","B7","B8"]
        colPos = ['center','center','center','center','center',tk.E,tk.E,tk.E,'center',tk.E,'center','center','center','center',
                  'center','center','center','center','center','center']
        self.display_cols = ["Send","Channel","Period","Restart","Total","Ext","CAN HEX ID","DLC","B1","B2","B3","B4","B5","B6","B7","B8"]
        self.can_tree = ttk.Treeview(self.can0_frame, selectmode = "browse",displaycolumns="#all",columns = self.colNames,height=40)
        
        self.can_tree.grid(row=0,column=0)

        self.can_tree.heading("#0", anchor = tk.W, text = "Label")
        for c,w,p in zip(self.colNames,colWidths,colPos):
            self.can_tree.column(c, anchor = p, stretch = False, width = w)
            self.can_tree.heading(c, anchor = p, text = c)
        self.item_identifier={}
        self.msg_index = 0
        self.current_iid = ('I-1',)
        self.new_message = True
        
        if self.settings_dict["CAN"]["Load Preprogrammed"]:
            #self.tx_msg_ids=[]
            msg_list = self.settings_dict["CAN"]["Preprogrammed"]
            
            for message_string in msg_list:
                self.load_can_frame(message_string,self.msg_index)
                time.sleep(0.002)
                self.msg_index+=1
                
        else:
            self.send_clear_can()
        
        self.can_tree.bind('<<TreeviewSelect>>',self.fill_can_box)

            
        self.message_config_frame = tk.LabelFrame(self.truck_networks_tab, name="network Configurations",
                                                  text="Network Configurations")
        self.message_config_frame.grid(row=6,column=1,sticky="NW",columnspan=1)

        self.lin_to_shield_switch = config_switches(self.message_config_frame,self.tx_queue,
                            self.settings_dict["Switches"],"LIN to SHLD",row=1,col=0)
        self.lin_to_port_16 = config_switches(self.message_config_frame,self.tx_queue,
                            self.settings_dict["Switches"],"LIN to Port 16",row=2,col=0)
        self.lin_to_master = config_switches(self.message_config_frame,self.tx_queue,
                            self.settings_dict["Switches"],"LIN Master Pullup Resistor",row=3,col=0)
        self.can0_term = config_switches(self.message_config_frame,self.tx_queue,
                            self.settings_dict["Switches"],"CAN0",row=4,col=0)
        self.can1_term = config_switches(self.message_config_frame,self.tx_queue,
                            self.settings_dict["Switches"],"CAN1",row=6,col=0)
        self.can2_term = config_switches(self.message_config_frame,self.tx_queue,
                            self.settings_dict["Switches"],"CAN2",row=5,col=0)
        self.j1708_switch = config_radio_switches(self.message_config_frame,self.tx_queue,
                            self.settings_dict["Switches"],"CAN1 or J1708",rowA=7,colA=0,rowB=8,colB=0)

    def modify_can_message(self,event=None):
        self.new_message=False
        can_thread = self.can_thread_value.get()
        selection = self.can_tree.selection()
        self.common_can_message(can_thread)
        self.sync_tables()
        
    def delete_can_message(self):
        selection = self.can_tree.selection()
        while self.can_tree.parent(selection) is not "":
            selection = self.can_tree.parent(selection)
        
        can_msg = self.can_tree.item(selection)
        commandString = "GO,{},0".format(self.can_thread_value.get()) 
        self.tx_queue.put_nowait(commandString)
        for tree_item in self.can_tree.get_children(selection):
            self.can_tree.delete(tree_item)
        self.can_tree.delete(selection)

    def add_sequential_message(self):
        self.new_message = True
        selection = self.can_tree.selection()
        if self.can_tree.parent(selection) is not "":
            while self.can_tree.next(selection) is not "":
                selection = self.can_tree.next(selection)
        self.can_tree.selection_set(selection)
        self.can_count_value.set("{}".format( self.get_max_count(selection) + 1 ))
        self.can_sub_value.set("{}".format( self.get_max_count(selection) ))
        can_thread = int(self.can_thread_value.get())
        self.common_can_message(str(can_thread))
        self.sync_tables()
        
    def sync_tables(self):
        selection = self.can_tree.selection()
        while self.can_tree.parent(selection) is not "":
            selection = self.can_tree.parent(selection)
        tree_item = selection
        
        self.can_tree.set(tree_item,"Count",str(self.can_count_value.get()))
        if self.can_send_state.get() == 1:
            state = "Yes"
        else:
            state = "No"
        self.can_tree.set(tree_item,"Send",state)
        if self.can_channel_value.get() == "0":
            chan = "J1939"
        elif self.can_channel_value.get() == "1":
            chan = "CAN2"
        self.can_tree.set(tree_item,"Channel",chan)
        self.can_tree.set(tree_item,"Period",self.can_period_value.get())
        self.can_tree.set(tree_item,"Restart",self.can_restart_value.get())
        self.can_tree.set(tree_item,"Total",self.can_total_value.get())
        for tree_item in self.can_tree.get_children(selection):
            self.can_tree.set(tree_item,"Count",str(self.can_count_value.get()))
            if self.can_send_state.get() == 1:
                state = "Yes"
            else:
                state = "No"
            self.can_tree.set(tree_item,"Send",state)
            if self.can_channel_value.get() == "0":
                chan = "J1939"
            elif self.can_channel_value.get() == "1":
                chan = "CAN2"
            self.can_tree.set(tree_item,"Channel",chan)
            self.can_tree.set(tree_item,"Period",self.can_period_value.get())
            self.can_tree.set(tree_item,"Restart",self.can_restart_value.get())
            self.can_tree.set(tree_item,"Total",self.can_total_value.get())
            
                     
    def create_new_message(self):
        self.new_message = True
        selection = self.can_tree.selection()
        can_thread_list=[]
        for selection in self.can_tree.get_children(""):
            can_msg = self.can_tree.item(selection)
            vals = can_msg['values']
            can_thread_list.append(vals[0])
        can_thread = self.get_max_threads() + 1
        self.can_sub_value.set("0")
        self.can_count_value.set("1")
        if can_thread < 1024:
            #self.create_can_message = False
            self.common_can_message(str(can_thread))
        else:
            print("Too many CAN threads for SSS2. Please redo the CAN messages.")

    def get_max_threads(self):
        can_thread_list=[]
        for selection in self.get_all_children(self.can_tree):
            can_msg = self.can_tree.item(selection)
            vals = can_msg['values']
            can_thread_list.append(vals[0])
        return  max(can_thread_list)

    def get_max_count(self,item):
        can_thread_list=[]
        can_msg = self.can_tree.item(item)
        vals = can_msg['values']
        can_thread_list.append(vals[1])
        for selection in self.can_tree.get_children(item):
            can_msg = self.can_tree.item(selection)
            vals = can_msg['values']
            can_thread_list.append(vals[1])
        return max(can_thread_list)
        
    def common_can_message(self,can_thread):
        #new_thread = from serial len(self.settings_dict["CAN"]["Load Preprogrammed"])
        m = ""
        m += self.can_name_value.get()
        m += ","
        m += can_thread 
        m += ","
        m += self.can_count_value.get()
        m += ","
        m += self.can_sub_value.get()
        m += ","
        m += self.can_channel_value.get()
        m += ","
        m += self.can_period_value.get()
        m += ","
        m += self.can_restart_value.get()
        m += ","
        m += self.can_total_value.get()
        m += ","
        m += str(self.can_ext_id_state.get())
        m += ","
        m += self.can_id_value.get()
        m += ","
        m += self.can_dlc_value.get()
        for i in range(8):
            m += ","
            m += self.can_byte_value[i].get()
        m += ","
        if self.can_send_state.get() == 1:
            m += "Yes"
        else:
            m += "No"
        
        self.load_can_frame(m,self.msg_index)
        
        #self.can_thread_value.set(self.thread_from_sss2)
        
        #print(m)
        self.settings_dict["CAN"]["Custom"].append(m)
        self.msg_index+=1
        
        
    def send_single_frame(self,event=None):
        commandString = "GO,{},{}".format(self.can_thread_value.get(),self.can_send_state.get()) 
        self.tx_queue.put_nowait(commandString)
        selection = self.can_tree.selection()
        if self.can_send_state.get():
             self.can_tree.set(selection,"Send","Yes")
        else:
              self.can_tree.set(selection,"Send","No")
        self.sync_tables()
            
    def fill_can_box(self,event=None):
        selection = self.can_tree.selection()
        can_msg = self.can_tree.item(selection)
        vals = can_msg['values']
        if len(vals)==19:
            self.can_thread_value.set(vals[0])
            self.can_count_value.set(vals[1])
            self.can_sub_value.set(vals[2])
            self.can_name_value.set(can_msg['text'])
            self.can_id_value.set(vals[9])
            self.can_dlc_value.set(vals[10])
            self.can_ext_id_state.set(vals[8])
            if vals[3]=="Yes":
                self.can_send_state.set(1)
            else:
                self.can_send_state.set(0)
            if vals[4] == "J1939":
                self.can_channel_value.set("0")
            else:
                self.can_channel_value.set("1")
            self.can_period_value.set(vals[5])
            self.can_restart_value.set(vals[6])
            self.can_total_value.set(vals[7])
            for i in range(8):
                self.can_byte_value[i].set(vals[11+i])
            self.modify_can_button.configure(state=tk.NORMAL)
        else:
            self.modify_can_button.configure(state=tk.DISABLED)

    def load_can_frame(self,message_string,msg_iid):
        
        msg = message_string.split(',')
        msgKey = msg[0].strip()
        index = msg[1].strip()
        
        num = msg[2].strip()
        sub = msg[3].strip()
        
        if msg[4] == "0":
            channel = "J1939"
        elif msg[4] == "1":
            channel = "CAN2"
        else:
            channel = msg[4].strip()
        period = msg[5].strip()
        restart = msg[6].strip()
        total = msg[7].strip()
        extID = msg[8].strip()
        IDhex = msg[9].strip()
        dlc = msg[10].strip()
        B=[]
        
        for b in msg[11:19]:
            B.append ("{:02X}".format(int(b,16)))
        send = msg[19].strip()

        if self.new_message:
            if sub == "0":
                selection = self.can_tree.insert("",int(index),iid=msg_iid,text=msgKey,open=True,
                                                    values=[index,num,"0",send,channel,period, restart,total,extID,IDhex,dlc]+B)    
                  
            else:
                self.trunk = self.can_tree.selection()
                while self.can_tree.parent(self.trunk) is not "":
                    self.trunk = self.can_tree.parent(self.trunk)
                selection = self.can_tree.insert(self.trunk,int(sub),iid=msg_iid,text=msgKey,open=True,
                                                values=[index,num,sub,send,channel,period, restart,total,extID,IDhex,dlc]+B)
        else:
            selection = self.can_tree.selection()
            self.item_identifier[msg_iid] = selection
            if self.can_tree.item(selection) is not "":
                self.can_tree.set(selection,"Send",send)
                self.can_tree.set(selection,"Channel",channel)
                self.can_tree.set(selection,"Period",period)
                self.can_tree.set(selection,"Restart",restart)
                self.can_tree.set(selection,"Total",total)
                self.can_tree.set(selection,"Ext",extID)
                self.can_tree.set(selection,"CAN HEX ID",IDhex)
                self.can_tree.set(selection,"DLC",dlc)
                for i in range(8):
                    self.can_tree.set(selection,"B{}".format(i+1),B[i])
          

        self.can_tree.selection_set(selection)
        #self.can_tree.selection_toggle(self.item_identifier[msg_iid])
        
        commandString = "SM,"+message_string
        self.tx_queue.put_nowait(commandString)    

        self.can_thread_value.set(index)
        if send == "Yes":
            self.can_send_state.set(1)
        else:
            self.can_send_state.set(0)

        self.send_single_frame()
















        
        
    def voltage_out_settings(self):
       
        self.DAC_bank = tk.LabelFrame(self.voltage_out_tab, name="dac_bank",
                                                  text="Voltage Outputs")
        self.DAC_bank.grid(row=0,column=0,sticky="NW",columnspan=1)
        self.DAC_bank.grid_rowconfigure(4,weight=2) #Expands blank space under radio buttons.

        dac_dict=self.settings_dict["DACs"]
        self.dac_objects={}
        for key,c,r in zip(sorted(dac_dict.keys()),[0,1,2,3,0,1,2,3],[0,0,0,0,1,1,1,1]):
            self.dac_objects[key] = DAC7678(self.DAC_bank,self.tx_queue, dac_dict[key], row=r, col=c)
        
        self.vout2a_switch = config_radio_switches(self.DAC_bank,self.tx_queue,
                            self.settings_dict["Switches"],"Port 10 or 19",rowA=2,colA=1,rowB=3,colB=1)
        self.vout2b_switch = config_radio_switches(self.DAC_bank,self.tx_queue,
                            self.settings_dict["Switches"],"Port 15 or 18",rowA=2,colA=0,rowB=3,colB=0)
        
        self.hvadjout_bank = tk.LabelFrame(self.DAC_bank, name="hvadjout_bank",
                                                  text="High Current Adjustable Regulator")
        self.hvadjout_bank.grid(row=2,column=3,sticky="E",columnspan=1,rowspan=3)
        self.hvadjout = DAC7678(self.hvadjout_bank,self.tx_queue, self.settings_dict["HVAdjOut"], row=0, col=0)
        
        self.pwm_bank=tk.LabelFrame(self.voltage_out_tab, name="pwm_bank",
                                                  text="Pulse Width Modulated (PWM) Outputs")
        self.pwm_bank.grid(row=2,column=0,sticky="NW",columnspan=1)

        self.pwm1_switch = config_switches(self.pwm_bank,self.tx_queue,
                            self.settings_dict["Switches"],"PWM1 Connect",row=1,col=0)
        self.pwm2_switch = config_switches(self.pwm_bank,self.tx_queue,
                            self.settings_dict["Switches"],"PWM2 Connect",row=1,col=1)
        self.pwm3_switch = config_radio_switches(self.pwm_bank,self.tx_queue,
                            self.settings_dict["Switches"],"PWM3 or 12V",rowA=1,colA=2,rowB=2,colB=2)
        
        self.pwm4_switch = config_radio_switches(self.pwm_bank,self.tx_queue,
                            self.settings_dict["Switches"],"PWM4 or Ground",rowA=1,colA=3,rowB=2,colB=3)
        
        self.pwm12_switch = config_radio_switches(self.pwm_bank,self.tx_queue,
                            self.settings_dict["Switches"],"PWMs or CAN2",rowA=2,colA=0,rowB=3,colB=0)
        self.pwm_objects={}
        pwm_dict=self.settings_dict["PWMs"]
        col_index=0
        for key in sorted(pwm_dict.keys()):
            self.pwm_objects[key] = pwm_out(self.pwm_bank,self.tx_queue, pwm_dict[key], row=0, col=col_index)
            col_index+=1
        
        
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
                                    name="stream CAN2 (E-CAN)",
                                    text="Stream CAN2 (E-CAN)",
                                    command=self.send_stream_can1)
        self.stream_can1_box.grid(row=6,column=0,sticky="NW")
        self.stream_can1_box.state(['!alternate']) #Clears Check Box
        
        
        self.stream_A21_box =  ttk.Checkbutton(self.serial_frame,
                                    name='stream_A21',
                                    text="Stream Port 10 Voltage Readings",
                                    command=self.send_stream_A21)
        self.stream_A21_box.grid(row=5,column=0,sticky="NW")
        self.stream_A21_box.state(['!alternate']) #Clears Check Box

        self.serial_window_lines = 300

        


        
    def send_stream_A21(self):
        if self.stream_A21_box.instate(['selected']):
            commandString = "SV,1"
        else:
            commandString = "SV,0"
        self.tx_queue.put_nowait(commandString)    
        
    

    def connect_to_serial(self):
        connection_dialog = setup_serial_connections(self)
        self.serial = connection_dialog.result
        print(self.serial)
        if self.serial: 
            if self.serial is not None:
                if self.serial.isOpen():
                    print("SSS2 connected")
                    
                    self.thread = SerialThread(self,self.rx_queue,self.tx_queue,self.serial)
                    self.thread.start()
                    print("Started Serial Thread.")
                    self.init_tabs()
                    return
           
        messagebox.showerror("SSS2 Serial Connection Error",
                              "The SSS2 serial connection is not present. Please connect the SSS2." )                
        self.init_tabs()    
        
    def check_serial_connection(self,event = None):
        if self.serial:
            available_comports = setup_serial_connections.find_serial_ports(self)
            for port in available_comports:
                if self.serial.port in port.split():
                    self.serial_connected = True
                    self.connection_status_string.set('SSS2 Connected on '+self.serial.port)
                    self.text['bg']='white'
                    self.serial_rx_entry['bg']='white'
                    return True
          
        self.connection_status_string.set('USB to Serial Connection Unavailable. Please install drivers and plug in the SSS2.')
        #self.serial_connected = False
        #self.serial = False
        
        self.text['bg']='red'
        self.serial_rx_entry['bg']='red'
        
        
        if self.serial: 
            if self.serial is not None:
                self.connect_to_serial()
            else:
                self.serial.close()
                
                
        return False
    
        self.after(2000,self.check_serial_connection())
        
    def send_arbitrary_serial_message(self,event = None):
        commandString = self.serial_TX_message.get()
        self.tx_queue.put_nowait(commandString)
        self.serial_TX_message.delete(0,tk.END)
        
##    def send_serial_command(self,commandString):
##        command_bytes = bytes(commandString,'ascii') + b'\n'
##        print(command_bytes)
##        if self.serial:
##            try:
##                self.serial.write(command_bytes)
##                return command_bytes    
##            except Exception as e:
##                print(e)
##                return False            
##        else:
##            return False

        
    def send_stream_can0(self):
        if self.stream_can0_box.instate(['selected']):
            commandString = "C0,1"
        else:
            commandString = "C0,0"
        self.tx_queue.put_nowait(commandString)

    def send_stream_can1(self):
        if self.stream_can1_box.instate(['selected']):
            commandString = "C1,1"
        else:
            commandString = "C1,0"
        self.tx_queue.put_nowait(commandString)
            
    def send_toggle_CAN(self):
        commandString = "DJ"
        self.tx_queue.put_nowait(commandString)

    def send_list_settings(self):
        commandString = "LS"
        self.tx_queue.put_nowait(commandString)
        
    def process_serial(self):
        gathered_bytes = len(self.serial_rx_byte_list)
        self.serial_RX_count.delete(0,tk.END)
        self.serial_RX_count.insert(0,gathered_bytes)

        if self.check_serial_connection():
            
            while self.rx_queue.qsize():
                new_serial_line = self.rx_queue.get_nowait()
                #print(new_serial_line)
                self.serial_rx_byte_list.append(new_serial_line)
                gathered_bytes = len(self.serial_rx_byte_list)
                if new_serial_line[0:5]==b'CAN 0':
                    self.received_can0_messages.append(new_serial_line)
                elif new_serial_line[0:5]==b'CAN 1':
                    self.received_can2_messages.append(new_serial_line)
                elif new_serial_line[:16]==b'OK:Authenticated':
                    self.file_authenticated = True
                    self.file_OK_received.set(True)
                elif new_serial_line[0:4]==b'OK:D':
                    self.file_authenticated = False
                    self.file_OK_received.set(True)
                elif new_serial_line[0:23]==b'INFO SSS2 Component ID:':
                    temp_data = str(new_serial_line,'utf-8').split(':')
                    self.sss_component_id_text.set(temp_data[1].strip())
                elif new_serial_line[0:8]==b'FIRMWARE':
                    temp_data = str(new_serial_line,'utf-8').split()
                    self.sss_software_id_text.set(temp_data[1].strip())
                elif new_serial_line[0:4]==b'ID: ':
                    temp_data = str(new_serial_line[4:],'utf-8')
                    self.sss2_product_code_text.set(temp_data)
                    self.sss2_product_code['bg']='white'
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
        row_index=0
        pot_dict=self.settings_dict["Potentiometers"]
        for bank_key in sorted(pot_dict.keys()):
            if bank_key == "Others":
                self.pot_bank[bank_key] = pot_bank(self.settings_tab,self.tx_queue,pot_dict,bank_key,row=row_index,col=1,colspan=1)
            else:
                self.pot_bank[bank_key] = pot_bank(self.settings_tab,self.tx_queue,pot_dict,bank_key,row=row_index,col=1,colspan=3)
            row_index += 1
 
        self.settings_tab.grid_columnconfigure(1,weight=2)
        self.switch_frame = tk.Frame(self.settings_tab, name='switch frame');
        self.switch_frame.grid(row=2,rowspan=1,column=1, columnspan=1,sticky="NE")

        
        self.twelve2_switch = config_switches(self.switch_frame,self.tx_queue,
                            self.settings_dict["Switches"],"12V Out 2",row=0,col=0)
        self.ground2_switch = config_switches(self.switch_frame,self.tx_queue,
                            self.settings_dict["Switches"],"Ground Out 2",row=1,col=0)
        
        
        angled_photo = tk.PhotoImage(file="sss2angle.gif")
        new_photo = angled_photo.subsample(2,2)
        
        image_label = Label(self.settings_tab,image=new_photo)
        image_label.image = new_photo
        image_label.grid(row=2,column=2,sticky=tk.E)

           
    

    def send_ignition_key_command(self,event=None):
        if self.ignition_key_button.instate(['selected']):
            commandString = "50,1"
        else:
            commandString = "50,0"
        self.tx_queue.put_nowait(commandString)
        
    
    def on_quit(self,event=None):
        """Exits program."""
        self.serialclose()
        quit()

class preprogrammed_message(SSS2):
    def __init__(self, parent,tx_queue,msg_dict,msg_id, row = 0, col = 0):
        self.root=parent
        self.tx_queue = tx_queue
        self.msg_dict = msg_dict
        self.msg_id = msg_id
        self.col=col
        self.row=row
        self.setup_messages()
    def setup_messages(self):
        label = " "
        for dat in self.msg_dict[self.msg_id]["Data"]:
            label += " {:02X}".format(dat)
        label+=", Period: {}ms, PGN: {}, SA: {}, Note:{}".format(self.msg_dict[self.msg_id]["Period"],
                                                            self.msg_dict[self.msg_id]["PGN Name"],
                                                            self.msg_dict[self.msg_id]["Source Address"],
                                                            self.msg_dict[self.msg_id]["Label"])
        
        self.box =  ttk.Checkbutton(self.root,
                                    text=self.msg_id,
                                    command=self.toggle_preprogrammed_can)
        self.box.grid(row=self.row,column=self.col,sticky="NW")
        self.box.state(['!alternate']) #Clears Check Box
        if self.msg_dict[self.msg_id]["State"]:
            self.box.state(['selected'])
        self.toggle_preprogrammed_can()

        datalabel = " "
        for dat in self.msg_dict[self.msg_id]["Data"]:
            datalabel += " {:02X}".format(dat)
        datalabel+=" "
        tk.Label(self.root,text=datalabel).grid(row=self.row,column=self.col+1,sticky=tk.W)
        tk.Label(self.root,text="{}ms ".format(self.msg_dict[self.msg_id]["Period"])).grid(row=self.row,column=self.col+2,sticky=tk.W)
        tk.Label(self.root,text="{} ".format(self.msg_dict[self.msg_id]["PGN Name"])).grid(row=self.row,column=self.col+3,sticky=tk.W)
        tk.Label(self.root,text="{} ".format(self.msg_dict[self.msg_id]["Source Address"])).grid(row=self.row,column=self.col+4,sticky=tk.W)
        tk.Label(self.root,text=self.msg_dict[self.msg_id]["Label"]).grid(row=self.row,column=self.col+5,sticky=tk.W)
        
    def toggle_preprogrammed_can(self):
        state = self.box.instate(['selected'])
        setting = self.msg_dict[self.msg_id]["Setting"]
        if state:
            commandString = "CN,{},1".format(setting)
        else:
            commandString = "CN,{},0".format(setting)
        self.tx_queue.put_nowait(commandString)
    
class pot_bank(SSS2):
    def __init__(self, parent,tx_queue,pot_dict,key, row = 0, col = 0,colspan=3):
        self.root=parent
        self.tx_queue = tx_queue
        self.pot_dict = pot_dict
        self.bank_key = key
        self.col=col
        self.row=row
        self.colspan=colspan
        self.setup_pot_bank()
    def setup_pot_bank(self):
        #Setup Bank with a common Switch for Terminal A
        label=self.pot_dict[self.bank_key]["Label"]
        self.pot_bank = tk.LabelFrame(self.root,name=label.lower(),text=label)
        self.pot_bank.grid(row=self.row,column=self.col,columnspan=self.colspan,sticky=tk.W)
        if self.pot_dict[self.bank_key]["Terminal A Connection"]:
            self.bank_button =  ttk.Checkbutton(self.pot_bank,
                                                text="Terminal A Voltage Enabled",
                                                name='terminal_A_voltage_connect',
                                                command=self.send_bank_term_A_voltage_command)
            self.bank_button.grid(row=0,column=0,sticky=tk.W)
            self.bank_button.state(['!alternate']) #Clears Check Box
            if self.pot_dict[self.bank_key]["Terminal A Connection"]:
                self.bank_button.state(['selected'])
            self.send_bank_term_A_voltage_command() #Call the command once

        self.pot_pairs={}
        col_index=0
        for key in sorted(self.pot_dict[self.bank_key]["Pairs"].keys()):
            self.pot_pairs[key] = potentiometer_pair(self.pot_bank,self.tx_queue,
                           self.pot_dict[self.bank_key]["Pairs"],
                           pair_id=key,col=col_index,row=1)
            col_index += 1
        
    def send_bank_term_A_voltage_command(self):
        state=self.bank_button.instate(['selected'])
        setting = self.pot_dict[self.bank_key]["SSS2 Setting"]
        if setting is not None:
            if state:
                commandString = "{:d},1".format(setting)
            else:
                commandString = "{:d},0".format(setting)
            self.tx_queue.put_nowait(commandString)

            
class config_switches(SSS2):
    def __init__(self, parent,tx_queue,switch_dict,key, row = 0, col = 0):
        self.root=parent
        self.tx_queue = tx_queue
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
        #self.switch_button_dict[self.key]["State"]=state
        SSS2_setting = self.switch_button_dict[self.key]["SSS2 setting"]
        if state:
            commandString = "{},1".format(SSS2_setting)
        else:
            commandString = "{},0".format(SSS2_setting)
        return self.tx_queue.put_nowait(commandString)

class config_radio_switches(SSS2):
    def __init__(self, parent,tx_queue,switch_dict,key, rowA = 0, colA = 0,
                 rowB = 0, colB = 1, rowspanA=2, rowspanB=2,
                 colspanA=1, colspanB=1,):
        self.root=parent
        self.tx_queue =tx_queue
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
        #self.switch_button_dict[self.key]["State"]=state
        SSS2_setting = self.switch_button_dict[self.key]["SSS2 setting"]
        if state:
            commandString = "{},1".format(SSS2_setting)
        else:
            commandString = "{},0".format(SSS2_setting)
        return self.tx_queue.put_nowait(commandString)   

  
class potentiometer_pair(SSS2):
    def __init__(self, parent,tx_queue,pair_dict,pair_id, row = 0, col = 0):
        self.root = parent
        self.tx_queue = tx_queue
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
            
            
            self.five_volt_switch = ttk.Radiobutton(self.potentiometer_pair, text="+5V", value="+5V",
                                                command=self.send_terminal_A_voltage_command,
                                                    name='button_5',
                                                    variable = self.terminal_A_setting)
            self.five_volt_switch.grid(row=0,column = 1,sticky=tk.W)
            if self.pair_dict["Terminal A Voltage"] == "+5V":
                self.five_volt_switch.state(['selected'])
                self.terminal_A_setting.set("+5V")
            else:
                self.twelve_volt_switch.state(['selected'])
                self.terminal_A_setting.set("+12V")
            self.send_terminal_A_voltage_command() #run once
        else:
            self.twelve_volt_switch = None

        col_count = 0
        self.pots={}
        for key in sorted(self.pair_dict["Pots"].keys()):
            self.pots[key] = potentiometer(self.potentiometer_pair,self.tx_queue, self.pair_dict["Pots"][key], row=1, col=col_count)
            col_count+=1

    def send_terminal_A_voltage_command(self):
        
        new_setting = self.terminal_A_setting.get()
        if new_setting == "+5V":
            commandString = "{},0".format(self.pair_dict["SSS Setting"])
        else:
            commandString = "{},1".format(self.pair_dict["SSS Setting"])
        return self.tx_queue.put_nowait(commandString)

class potentiometer(SSS2):
    def __init__(self, parent,tx_queue, pot_dict, row = 2, col = 0):
        self.root = parent
        self.tx_queue = tx_queue
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
        tk.Label(self.potentiometer_frame,text="Wiper Position",name="wiper label").grid(row=2,column=1, sticky="SW",columnspan=2)
        tk.Label(self.potentiometer_frame,text=self.pot_settings_dict["Resistance"],
                 name="wiper resistance").grid(row=2,column=2, sticky="NE",columnspan=1)
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
                                                          text="Connected to Ground",
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
        self.tx_queue.put_nowait(commandString)
    
    def set_terminals(self):
        self.terminal_A_connect_state = self.terminal_A_connect_button.instate(['selected'])
        self.terminal_B_connect_state = self.terminal_B_connect_button.instate(['selected'])
        self.wiper_connect_state = self.wiper_connect_button.instate(['selected'])
        terminal_setting = self.terminal_B_connect_state + 2*self.wiper_connect_state + 4*self.terminal_A_connect_state
        commandString = "{},{}".format(self.tcon_setting,terminal_setting)
        self.tx_queue.put_nowait(commandString)
        

class DAC7678(SSS2):
    def __init__(self, parent,tx_queue,sss2_settings, row = 2, col = 0):
        self.root = parent
        self.tx_queue = tx_queue
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
        return self.tx_queue.put_nowait(commandString)
        
    
    def set_dac_mean_slider(self,event=None):
        entry_value = self.dac_mean_position_value.get()
        self.dac_mean_position_value['foreground'] = "black"
        try:
            self.dac_mean_slider.set(float(entry_value)*100)
        except Exception as e:
            print(e)
            self.root.bell()
            self.dac_mean_position_value['foreground'] = "red"


class pwm_out(SSS2):
    def __init__(self, parent,tx_queue,sss2_settings, row = 2, col = 0):
        self.root = parent
        self.tx_queue = tx_queue
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
        self.set_pwm_duty_cycle_slider()

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
        self.set_pwm_frequency_slider()

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
        self.tx_queue.put_nowait(commandString)
        return commandString

    def set_pwm_duty_cycle(self,event=None):
             
        self.pwm_duty_cycle_value.delete(0,tk.END)
        self.pwm_duty_cycle_value.insert(0,self.pwm_duty_cycle_slider.get())
        
        slope = 4096/100
        pwm_raw_setting = int(slope*(float(self.pwm_duty_cycle_value.get())))
        commandString = "{},{}".format(self.setting_num,pwm_raw_setting)
        self.tx_queue.put_nowait(commandString)
        return commandString

    def set_pwm_frequency_slider(self,event=None):
        entry_value = self.pwm_frequency_value.get()
        self.pwm_frequency_value['foreground'] = "black"
        try:
            self.pwm_frequency_slider.set(float(entry_value))
        except Exception as e:
            print(e)
            self.root.bell()
            self.pwm_frequency_value['foreground'] = "red"
    
    def set_pwm_duty_cycle_slider(self,event=None):
        entry_value = self.pwm_duty_cycle_value.get()
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

        

        
if __name__ == '__main__':

    root = tk.Tk()
    mainwindow = SSS2(root,name='sss2')
    root.mainloop()
    try:
        root.destroy() # if mainloop quits, destroy window
    except:
        print("Bye.")
