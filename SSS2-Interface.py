import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
import serial
import serial.tools.list_ports
import os
import sys
import threading
import queue
import time
import string
import hashlib
from pprint import pformat
import re
import getpass
import webbrowser
from operator import itemgetter
import struct

from tkinter.tix import *
from tkinter.constants import *
import tkinter.scrolledtext as tkst
import collections

from SSS2_defaults import *
            
class SerialThread(threading.Thread):
    def __init__(self, parent, rx_queue, tx_queue,serial):
        self.root = parent
        threading.Thread.__init__(self)
        self.rx_queue = rx_queue
        self.tx_queue = tx_queue
        self.serial=serial
        self.signal = True
        
    def run(self):
        time.sleep(.1)
        needsMore = False
        try:
            while self.serial.is_open and self.signal:           
                if self.tx_queue.qsize():
                    s = self.tx_queue.get_nowait()
                    self.serial.write(bytes(s,'utf-8') + b'\x0A')
                    time.sleep(.0015) #ensure the listener can process the commands.
                    print('TX: ', end='')
                    print(s)
                if self.serial.in_waiting:
                    lines = self.serial.readlines(self.serial.in_waiting)
                    
                    for line in lines:
                        
                        if line[0:3] == b'CAN': 
                            canline = line[3:]
                            if len(canline) == 22:
                                self.rx_queue.put(self.getCANstring(canline))
                                canline = b''
                                needsMore = False
                                continue
                            else:
                                needsMore = True
                        if needsMore:
                            canline+=line
                            if len(canline) == 22:
                                #print("Complete CAN String")
                                self.rx_queue.put(self.getCANstring(canline))
                                canline = b''
                                needsMore = False
                                continue
                            else:
                                needsMore = True
                        else:
                            self.rx_queue.put(line)
                time.sleep(.001) #add a sleep statement to reduce CPU load for this thread.
                
        except Exception as e:
            print(e)
            print("Serial Connection Broken. Exiting Thread.")
            self.serial.close()
            self.serial.__del__()

        print("Serial Connection Closed.")
        self.serial.__del__()
        self.signal = False
    def getCANstring(self,databytes):
        
        channel = databytes[4]
        now = struct.unpack('>L',databytes[0:4])[0]
        fractions = struct.unpack('>L',b'\x00'+databytes[5:8])[0]
        canID = struct.unpack('>L',databytes[8:12])[0] & 0x1FFFFFFF
        extended = (databytes[8] & 0x80) >> 7
        length = databytes[12]
        
        line = "CAN{:d} {:d}.{:06d}".format(channel,now,fractions)
        line+= " {:08X}".format(canID)
        line+= " {:d}".format(extended)
        line+= " {:d}".format(length)
        for d in databytes[13:21]:
            line+= " {:02X}".format(d)
        line+= "\n"
        #print(line,end='')
        return bytearray(line,'ascii')
        
        

class setup_serial_connections(tk.Toplevel):
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.transient(parent)
        self.title("Connect")
        self.parent = parent
        self.result = None

        self.serial_frame = tk.Frame(self)
        self.buttonbox()
        self.serial_frame.pack(padx=5, pady=5)
        
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+150,
                                  parent.winfo_rooty()+150))
       
        self.serial=False

        self.grab_set()
        self.focus_set()
        self.wait_window(self)

    
    def buttonbox(self):
       

        self.connect_button = tk.Button(self.serial_frame, name='connect_button',
                                   text="Connect", width=10, command=self.ok, default=ACTIVE)
        self.connect_button.grid(row=3,column=0, padx=5, pady=5)
        cancel_button = tk.Button(self.serial_frame, text="Cancel", width=10, command=self.cancel)
        cancel_button.grid(row=3,column=1, padx=5, pady=5)
        
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        self.connect_button.focus()
        
        tk.Label(self.serial_frame,text="SSS2 COM Port").grid(row=0,column=0,columnspan=2)
        self.port_combo_box = ttk.Combobox(self.serial_frame,name="serial_port", 
                                           text="SSS2 COM Port")
        self.port_combo_box.grid(row=1,column=0,columnspan=2)
        self.populate_combo_box()
        
       

    def find_serial_ports(self):
        comPorts = []
        comPorts.append("Not Available")
        for possibleCOMPort in sorted(serial.tools.list_ports.comports()):
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
            self.focus_set() 
            return

        self.withdraw()
        self.update_idletasks()

        self.apply() #usually this is in the OK function

        self.cancel()
        
    def cancel(self, event=None):
        
        # put focus back to the parent window
        
        self.parent.focus_set()
        self.destroy()

    # command hooks

    def validate(self):
        if self.port_combo_box.get() == "Not Available":
            messagebox.showerror("SSS2 Serial Connection Error",
                   "SSS2 Connection is not available. Please plug in the SSS2 and be sure the drivers are installed." )
            self.result= None
            
        else:
            try:
                comport=(self.port_combo_box.get().split(" "))[0]

                with open("SSS2comPort.txt","w") as comFile:
                    comFile.write("{}".format(comport))
                
                ser = serial.Serial(comport,baudrate=4000000,timeout=0.010,
                                    parity=serial.PARITY_ODD,write_timeout=.010,
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

def update_dict(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            default = v.copy()
            default.clear()
            r = update_dict(d.get(k, default), v)
            d[k] = r
        else:
            d[k] = v
    return d

class SSS2(ttk.Frame):
    """The SSS2 gui and functions."""
    def __init__(self, parent, *args, **kwargs):
        self.frame_top = ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        self.root.geometry('1492x770+0+0')
        #self.root.geometry('+0+0')
        self.root.resizable(width=False, height=False)
        self.root.iconbitmap('synerconlogo.ico')
        self.settings_dict = get_default_settings()
        self.wiring_dict = get_default_wiring()
        self.root.title('Smart Sensor Simulator Interface')
        self.grid( column=0, row=0, sticky='NSEW') #needed to display
        #self.root.lift()
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.home_directory = os.path.expanduser('~')+os.sep+"Documents"+os.sep+"SSS2"+os.sep
        if not os.path.exists(self.home_directory):
            self.home_directory = os.path.expanduser('~')+os.sep
        os.path.normpath(self.home_directory)
        self.filename = None
        self.lasthash = None
        self.file_authenticated = False
        self.file_OK_received = tk.BooleanVar(name='file_OK_received')
        self.file_OK_received.set(False)
        self.autosave_job = None
        self.update_job = None
        self.unique_ID = None
        self.baudrates = ["250000","500000","666666","125000","1000000","5000","10000","20000","31520","333333","40000","50000","80000","100000","200000"]
        self.can2_baud_value=tk.StringVar(value="250000")
        self.can1_baud_value=tk.StringVar(value="250000")
        self.j1939_baud_value=tk.StringVar(value="250000")
        self.settings_file_status_string = tk.StringVar(value="Default Settings Loaded")
        self.file_loaded = False
        self.release_date = "03 June 2017"
################# Use this for production
        self.release_version = "1.0"
################## Use this for Universal
        #self.release_version = "1.0 UNIVERSAL" 
        self.connection_status_string = tk.StringVar(name='status_string',value="Not Connected.")
        connection_status_string = self.connection_status_string
        self.serial_rx_entry = tk.Entry(self,width=60,name='serial_monitor')
        serial_rx_entry = self.serial_rx_entry
        self.sss_component_id_text = tk.StringVar(value = self.settings_dict["Component ID"])
        self.sss_software_id_text = tk.StringVar(value = self.settings_dict["Software ID"])
        self.init_gui()
        
 
    def init_gui(self):
        """Builds GUI."""
        
        self.tx_queue = queue.Queue()
        self.rx_queue = queue.Queue()
       

        # Button to do something on the right
        self.ignition_key_button =  ttk.Checkbutton(self,name='ignition_key_switch',
                                            text="Ignition Key Switch",
                                            command=self.send_ignition_key_command)
        self.ignition_key_button.grid(row=0,column=0, padx=10, pady =5,sticky="w")
        self.ignition_key_button.state(['!alternate']) #Clears Check Box
        
        
        ttk.Label(self, text='USB/Serial Monitor:').grid(row=0,column=1,sticky=tk.E)
        #self.serial_rx_entry = tk.Entry(self,width=60,name='serial_monitor')
        self.serial_rx_entry.grid(row=0,column=2,sticky=tk.W+tk.E)
        
        self.tabs = ttk.Notebook(self, name='tabs')
        self.tabs.grid(row=1,column=0,columnspan=3,sticky=tk.W)

        self.file_status_string = tk.StringVar(value="Default Settings Loaded")
        tk.Label(self, textvariable=self.file_status_string, name="file_status_label").grid(row=2,column=0,sticky=tk.W)

        #self.connection_status_string = tk.StringVar(name='status_string',value="Not Connected.")
        tk.Label(self, textvariable=self.connection_status_string,name="connection_label").grid(row=2,column=2,sticky="E")

        self.modified_entry_string = tk.StringVar(name='modified_string',value="")
        self.modified_entry = tk.Entry(self, textvariable=self.modified_entry_string)
        self.modified_entry.grid(row=2,column=1)
        self.modified_entry['justify']=tk.CENTER
        

        
        # create each Notebook tab in a Frame
        #Create a Settings Tab to amake the adjustments for sensors
        self.profile_tab = tk.Frame(self.tabs, name='profile_tab')
        self.tabs.add(self.profile_tab, text="ECU Profile Settings") # add tab to Notebook

        #Create a Potentiometers Tab to amake the adjustments for sensors
        self.settings_tab = tk.Frame(self.tabs, name='potentiometer_tab')
        self.tabs.add(self.settings_tab, text="Digital Potentiometers") # add tab to Notebook
         
        #Create an additional Tab to interface with the SSS
        self.extra_tab = tk.Frame(self.tabs, name='extra_tab')
        self.tabs.add(self.extra_tab, text="Extra Outputs") # add tab to Notebook
        
        #Create a Voltage out make the adjustments for PWM, DAC, and Regulators
        self.voltage_out_tab = tk.Frame(self.tabs, name='voltage_out_tab')
        self.tabs.add(self.voltage_out_tab, text="Voltage Output") # add tab to Notebook
        
        #Create a Networks Tab to make the adjustments for J1939, CAN and J1708
        self.truck_networks_tab = tk.Frame(self.tabs, name='truck_network_tab')
        self.tabs.add(self.truck_networks_tab, text="Network Message Generator") # add tab to Notebook

        #Create a Connections Tab to interface with the SSS
        self.data_logger_tab = tk.Frame(self.tabs, name='data_logger')
        self.tabs.add(self.data_logger_tab, text="Data Logger") # add tab to Notebook

        #Create a Monitor Tab to interface with the SSS
        self.monitor_tab = tk.Frame(self.tabs, name='monitor tab')
        self.tabs.add(self.monitor_tab, text="SSS2 Command Interface") # add tab to Notebook

        

        self.tabs.enable_traversal()
        
          
        self.root.option_add('*tearOff', 'FALSE')
        self.menubar = tk.Menu(self.root,name='main_menus')
 
        self.menu_file = tk.Menu(self.menubar)
        self.menu_connection = tk.Menu(self.menubar)
        self.menu_tools = tk.Menu(self.menubar)
        
        self.menu_file.add_command(label='Open...', command=self.open_settings_file, accelerator="Ctrl+O")
        self.menu_file.add_command(label='Save', command=self.save_settings_file, accelerator="Ctrl+S")
        self.menu_file.add_command(label='Save As...', command=self.saveas_settings_file, accelerator="Ctrl+A")
        self.menu_file.add_command(label='Save Serial Log', command=self.save_log_file, accelerator="Ctrl+L")
        self.menu_file.add_command(label='Print as Text', command=self.print_settings_file, accelerator="Ctrl+P")
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Refresh', command=self.init_tabs, accelerator="Ctrl+R")
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Exit', command=self.root.quit, accelerator="Ctrl+Q")
        self.menu_connection.add_command(label='Select COM Port',
                                         command=self.connect_to_serial)
        self.menu_connection.add_separator()
        self.menu_connection.add_command(label='Get Unique ID',
                                         command=self.get_sss2_unique_id)
        self.menu_tools.add_command(label='Export Wiring Table',
                                         command=self.export_wiring)
        
        self.menubar.add_cascade(menu=self.menu_file, label='File')
        self.menubar.add_cascade(menu=self.menu_connection, label='Connection')
        self.menubar.add_cascade(menu=self.menu_tools, label='Tools')

        self.bind_all("<Control-o>",self.open_settings_file)
        self.bind_all("<Control-s>",self.save_settings_file)
        self.bind_all("<Control-a>",self.saveas_settings_file)
        self.bind_all("<Control-r>",self.init_tabs)
        self.bind_all("<Control-q>",self.on_quit)
        self.bind_all("<Control-k>",self.send_ignition_key_command)
        self.bind_all("<Control-l>",self.save_log_file)
        self.bind_all("<Control-p>",self.print_settings_file)
        
        self.root.config(menu=self.menubar)

        self.serial_connected = False
        self.serial_rx_byte_list = []
        self.received_can0_messages=[]
        self.received_can1_messages=[]
        self.received_can2_messages=[]
        self.received_j1708_messages=[]
        self.received_lin_messages=[]
        self.received_analog_messages=[]

        self.settings_monitor_setup()
        self.data_logger()
        self.potentiometer_settings()
        self.connect_to_serial()
        self.process_serial()
        self.tx_queue.put_nowait("Time,{:d}".format( int( time.time() - time.timezone + time.daylight*3600 )))
        self.init_tabs()
        
    def init_tabs(self,event=None):
        self.tx_queue.put_nowait("50,0")
        time.sleep(.25)
        
        if self.autosave_job is not None:
            self.after_cancel(self.autosave_job)
            self.autosave_job = None
        if self.update_job is not None:
            self.after_cancel(self.update_job)
            self.update_job = None

        for child in self.settings_tab.winfo_children():
            child.destroy()        
        for child in self.voltage_out_tab.winfo_children():
            child.destroy()
        for child in self.truck_networks_tab.winfo_children():
            child.destroy()

        self.send_stream_A21()
        self.send_stream_can0()
        self.send_stream_can1()
        self.send_stream_j1708()

        
        self.potentiometer_settings() #put this after the serial connections

        self.voltage_out_settings()

        self.vehicle_networks_settings()

        self.profile_settings()

        self.tabs.select(self.data_logger_tab)
        self.tabs.select(self.truck_networks_tab)
        self.tabs.select(self.voltage_out_tab)
        self.tabs.select(self.settings_tab)
        self.tabs.select(self.profile_tab)

        self.clear_j1939_buffer()
        self.clear_can2_buffer()
        self.clear_j1708_buffer()
        self.clear_analog_buffer()

        self.get_sss2_component_id()
        time.sleep(.05)
        self.get_sss2_software_id()

        time.sleep(.1)
        self.update_sha()
        if self.filename is not None:
            self.autosave()

       #Use these messages to determine window size during development.  
       # print("Window Height: {}".format(self.root.winfo_height()))
       # print("Window Width: {}".format(self.root.winfo_width()))

    def export_wiring(self):
        for group_key in self.settings_dict["Potentiometers"]:
            for pair_key in self.settings_dict["Potentiometers"][group_key]["Pairs"]:
                for pot_key in self.settings_dict["Potentiometers"][group_key]["Pairs"][pair_key]["Pots"]:
                    pot = self.settings_dict["Potentiometers"][group_key]["Pairs"][pair_key]["Pots"][pot_key]
                    self.wiring_dict[pot["Pin"]]={"Wire Color":pot["Wire Color"],"Application":pot["Application"],"ECU Pins":pot["ECU Pins"]}
        for dac_key in self.settings_dict["DACs"]:
            dac = self.settings_dict["DACs"][dac_key]
            self.wiring_dict[dac["Pin"]]={"Wire Color":dac["Wire Color"],"Application":dac["Application"],"ECU Pins":dac["ECU Pins"]}
        for pwm_key in self.settings_dict["PWMs"]:
            pwm = self.settings_dict["PWMs"][pwm_key]
            self.wiring_dict[pwm["Pin"]]={"Wire Color":pwm["Wire Color"],"Application":pwm["Application"],"ECU Pins":pwm["ECU Pins"]}
        pwm = self.settings_dict["HVAdjOut"]
        self.wiring_dict[pwm["Pin"]]={"Wire Color":pwm["Wire Color"],"Application":pwm["Application"],"ECU Pins":pwm["ECU Pins"]}
        
        types = [('Tab delimited file', '*.txt')]
        idir = self.home_directory
        ifile = "SSS2 Partial Wiring Table"
        title='SSS2 Wiring Table'
        wiring_filename = filedialog.asksaveasfilename( filetypes=types,
                                           initialdir=idir,
                                           initialfile=ifile,
                                           title=title,
                                           defaultextension=".txt")
        w=self.wiring_dict
        formatted_keys={}
        for key in w:
            cavity=key.split(":")
            formatted_keys[key]="{}:{:02d}".format(cavity[0],int(cavity[1]))
        sorted_keys = sorted(formatted_keys.items(), key=itemgetter(1))    
        with open(wiring_filename,'w') as f:
            f.write("Molex Pins\tColor\tApplication\tECU Pins\n")
            for key,label in sorted_keys:
                f.write("\t".join([formatted_keys[key],w[key]["Wire Color"],w[key]["Application"],w[key]["ECU Pins"]])+"\n")
        print("Saved "+wiring_filename)
        self.file_status_string.set("Saved "+wiring_filename)
            
    def print_settings_file(self,event=None):
        try:
            original_file = self.filename
            self.filename += ".txt"
            self.save_settings_file()
            os.startfile(self.filename, "open")
            print("Saved and opened "+self.filename)
            
        except Exception as e:
            print(e)
            messagebox.showerror("Print File Error",
                           "There is not a default application to print text (.txt) files. Please configure your system environment to print text files.")
                        
            
    def open_settings_file(self,event=None):
          
        types = [('Smart Sensor Simulator 2 Settings Files', '*.SSS2'),('All Files', '*')]
        idir = self.home_directory
        ifile = self.filename
        title='SSS2 Settings File'
        self.filename = filedialog.askopenfilename(filetypes=types,
                                                     initialdir=idir,
                                                     initialfile=ifile,
                                                     title=title,
                                                     defaultextension=".SSS2")
      
        try:
            with open(self.filename,'r') as infile:
                new_settings_dict=json.load(infile)

            if (len(new_settings_dict["Analog Calibration"]) < len(self.settings_dict["Analog Calibration"])):
                new_settings_dict["Analog Calibration"] = self.settings_dict["Analog Calibration"]
            
            self.settings_dict = update_dict(self.settings_dict,new_settings_dict)
            
        except Exception as e:
            print(e)
            messagebox.showerror("Loading File Error",
                           "The file selected is not the appropriate type for this program. This file may have been corrupted. The file must be a correctly formatted JSON file. Please select a different file.")
                        
            return

        digest_from_file=self.settings_dict["SHA256 Digest"]
        print("digest_from_file: ",end='')
        print(digest_from_file)
        
        newhash=self.get_settings_hash()

        print("newhash:          ",end='')
        print(newhash)
        
        #self.load_settings_file()
        ok_to_open = False
############### Use this for Universal       
        #if True:
############### Use this for Production       
        if newhash==digest_from_file:
            print("Hash digests match.")
            sss2_id = self.settings_dict["SSS2 Product Code"].strip()
            if  sss2_id == "UNIVERSAL":
                ok_to_open = True
            else:
                try:
                    if self.serial.isOpen():
                        
                        command_string = "OK,{}".format(sss2_id)
                        self.tx_queue.put_nowait(command_string)
                        self.wait_variable(self.file_OK_received)       
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
                            self.sss2_product_code['bg']='white'
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
            self.file_status_string.set("Opened "+self.filename)
            self.settings_file_status_string.set(os.path.basename(self.filename))
            print("Opened "+self.filename)
            self.settings_dict["SHA256 Digest"]=self.get_settings_hash()

        else:
            self.settings_dict = get_default_settings()    

        
        self.init_tabs()
        
        
    
    def saveas_settings_file(self,event=None):
        types = [('Smart Sensor Simulator 2 Settings Files', '*.SSS2')]
        idir = self.home_directory
        ifile = self.filename
        title='SSS2 Settings File'
        self.filename = filedialog.asksaveasfilename( filetypes=types,
                                           initialdir=idir,
                                           initialfile=ifile,
                                           title=title,
                                           defaultextension=".SSS2")
        self.save_settings_file()

    def save_settings_file(self,event=None):

        if self.filename is None:
            self.saveas_settings_file()

        if self.filename is '':
            self.file_status_string.set("File not saved.")
            print("File not saved.") 
            return
        
        ok_to_save = False
        sss2_id = self.sss2_product_code_text.get().strip()
        ###Take out this Conditional for production
        if not sss2_id == "UNIVERSAL":
                if self.serial is not None:
                    command_string = "OK,{}".format(sss2_id.strip())
                    self.tx_queue.put_nowait(command_string)
                    self.wait_variable(self.file_OK_received)       
                    self.file_OK_received.set(False)
                    if self.file_authenticated: 
                        ok_to_save = True
                    print("Authenticated. OK to Save")
        else:
################# Use this for UNIVERSAL     
            #ok_to_save = True ###Change to False for production
################# Use this for Production
            ok_to_save = False 
        if ok_to_save:
            self.settings_dict["SSS2 Interface Release Date"] = self.release_date
            self.settings_dict["SSS2 Interface Version"] = self.release_version

            self.interface_date.set(self.release_date)
            self.interface_release.set(self.release_version)
            
            self.file_status_string.set("Saved "+self.filename)
            self.settings_file_status_string.set(os.path.basename(self.filename))
            
            print("Saved "+self.filename)
            self.sss2_product_code['bg']='white'

            self.saved_date_text.set(time.strftime("%A, %d %B %Y %H:%M:%S %Z", time.localtime()))
            self.update_dict()
            self.settings_dict["SHA256 Digest"]=self.get_settings_hash()
            self.settings_dict["Original File SHA"]=self.settings_dict["SHA256 Digest"]
            

             
            with open(self.filename,'w') as outfile:
                json.dump(self.settings_dict,outfile,indent=4,sort_keys=True)

            
        

        else:
            self.file_status_string.set("")
            self.file_status_string.set("File not saved.")
            print("File not saved.") 
            messagebox.showerror("Incompatible SSS2 for Saving",
                            "The unique ID entered for the SSS2 does not match the unit. Please select Get ID from the Connection menu to get the SSS2 Unique ID to populate the form.")
            self.tabs.select(self.profile_tab)
            self.sss2_product_code.focus()
            self.sss2_product_code['bg']='yellow'
        
    def save_log_file(self,event=None):
        ifile = "SSS2_Log_{}.log".format(time.strftime("%Y-%m-%d_%H%M%S", time.localtime()))
        if os.path.exists(self.home_directory):
            log_filename = self.home_directory + ifile
        else:
            log_filename = os.path.expanduser('~') + os.sep + ifile
        with open(log_filename,'w') as log_file:
            for byte_entry in self.serial_rx_byte_list:
                log_file.write(byte_entry.decode('ascii',"ignore"))
        print("Saved {}".format(log_filename))
        self.file_status_string.set("Saved log data to "+log_filename)
                       
    def get_settings_hash(self):
        digest_from_file=self.settings_dict["Original File SHA"]
        load_date = self.settings_dict["Original Creation Date"]
        save_date = self.settings_dict["Saved Date"]
        
         
        
        self.settings_dict.pop("SHA256 Digest",None)
        self.settings_dict.pop("Original File SHA",None)
        self.settings_dict.pop("Original Creation Date",None)
        self.settings_dict.pop("Saved Date",None)
        sss_software_ID = self.settings_dict.pop("Software ID",None)
        sss_component_ID = self.settings_dict.pop("Component ID",None)
        sss_component_ID = self.settings_dict.pop("Serial Number",None)
        
        temp_settings_dict = pformat(self.settings_dict)
        new_hash = str(hashlib.sha256(bytes(temp_settings_dict,'utf-8')).hexdigest())
        
        self.settings_dict["SHA256 Digest"] = new_hash
        self.settings_dict["Original File SHA"] = digest_from_file
        self.settings_dict["Original Creation Date"] = load_date
        self.settings_dict["Saved Date"]=save_date
        self.settings_dict["Component ID"] =sss_component_ID
        self.settings_dict["Software ID"] = sss_software_ID
        self.settings_dict["Serial Number"] = sss_component_ID

        if self.settings_dict["Original File SHA"] ==  "Current Settings Not Saved.":
            self.modified_entry_string.set("Default Settings")
            self.modified_entry['bg']='yellow'
        else:
            if digest_from_file == new_hash:
                self.modified_entry_string.set("Settings Unchanged")
                self.modified_entry['bg']='light green'
            else:
                self.modified_entry_string.set("Settings Altered")
                self.modified_entry['bg']='red'
        
        return new_hash

    def autosave(self):
        if self.lasthash != self.current_hash:
            original_file = self.filename
            try:
                if self.filename[-14:] == ".SSS2.AUTOSAVE":
                    original_file = self.filename[:-14]
                else:
                    self.filename += ".SSS2.AUTOSAVE"
            except Exception as e:
                print(e)
                self.filename += ".SSS2.AUTOSAVE"
            with open(self.filename,'w') as outfile:
                json.dump(self.settings_dict,outfile,indent=4,sort_keys=True)
            self.filename = original_file
            #print('Autosaving')
            
        self.lasthash = self.current_hash 
        
        self.autosave_job = self.after(5000,self.autosave)

    def update_sha(self):
        self.update_dict()
        self.file_sha_string.set(self.settings_dict["Original File SHA"])
        self.current_hash = self.get_settings_hash()
        self.settings_sha_string.set(self.current_hash)

        self.update_job = self.after(500,self.update_sha)
        
    def enable_can_component_id(self):
        commandString = "CANCOMP,{}".format(self.can_component_id_text.get())
        self.tx_queue.put_nowait(commandString)

    def profile_settings(self):
        self.ecu_frame = tk.LabelFrame(self.profile_tab, name="ecu_frame",
                                                  text="Electronic Control Unit (ECU) Settings")
        self.ecu_frame.grid(row=0,column=0,sticky=tk.E+tk.W,columnspan=1)
        #User Changable values
        tk.Label(self.ecu_frame,text="ECU Year:").grid(row=0,column=0,sticky=tk.W)
        self.ecu_year_text = tk.StringVar(value = self.settings_dict["ECU Year"])
        self.ecu_year = tk.Entry(self.ecu_frame,textvariable= self.ecu_year_text, width=5)
        self.ecu_year.grid(row=0,column=1,sticky=tk.W,padx=5,pady=5)

        tk.Label(self.ecu_frame,text="ECU Make:").grid(row=0,column=3,sticky=tk.E)
        self.ecu_make_text = tk.StringVar(value = self.settings_dict["ECU Make"])
        self.ecu_make = tk.Entry(self.ecu_frame,textvariable= self.ecu_make_text, width=16)
        self.ecu_make.grid(row=0,column=4,sticky=tk.W,padx=5,pady=5)

        tk.Label(self.ecu_frame,text="ECU Model:").grid(row=0,column=5,sticky=tk.E)
        self.ecu_model_text = tk.StringVar(value = self.settings_dict["ECU Model"])
        self.ecu_model = tk.Entry(self.ecu_frame,textvariable= self.ecu_model_text, width=24)
        self.ecu_model.grid(row=0,column=6,sticky=tk.W,padx=5,pady=5)

        tk.Label(self.ecu_frame,text="ECU Software Version:").grid(row=2,column=0,sticky=tk.W,columnspan=2)
        self.sss_ecu_id_text = tk.StringVar(value = self.settings_dict["ECU Software Version"])
        self.sss_ecu_id = tk.Entry(self.ecu_frame, textvariable= self.sss_ecu_id_text, width=74)
        self.sss_ecu_id.grid(row=2,column=2,sticky=tk.W,padx=5,pady=5,columnspan=6)
        #tk.Button(self.ecu_frame,text="Get SW",command=self.get_ecu_software_id).grid(row=2,column=8,sticky=tk.W,padx=5)

        tk.Label(self.ecu_frame,text="Engine Serial Number:").grid(row=1,column=0,sticky=tk.W,columnspan=2)
        self.engine_serial_text = tk.StringVar(value = self.settings_dict["Engine Serial Number"])
        self.engine_serial = tk.Entry(self.ecu_frame, textvariable= self.engine_serial_text, width=74)
        self.engine_serial.grid(row=1,column=2,sticky=tk.W,padx=5,pady=5,columnspan=6)
        
        tk.Label(self.ecu_frame,text="Veh. Year:").grid(row=3,column=0,sticky=tk.W)
        self.vehicle_year_text = tk.StringVar(value = self.settings_dict["Vehicle Year"])
        self.vehicle_year = tk.Entry(self.ecu_frame,textvariable= self.vehicle_year_text, width=5)
        self.vehicle_year.grid(row=3,column=1,sticky=tk.W,padx=5,pady=5)

        tk.Label(self.ecu_frame,text="Vehicle Make:").grid(row=3,column=3,sticky=tk.E)
        self.vehicle_make_text = tk.StringVar(value = self.settings_dict["Vehicle Make"])
        self.vehicle_make = tk.Entry(self.ecu_frame,textvariable= self.vehicle_make_text, width=20)
        self.vehicle_make.grid(row=3,column=4,sticky=tk.W,padx=5,pady=5)

        tk.Label(self.ecu_frame,text="Vehicle Model:").grid(row=3,column=5,sticky=tk.E)
        self.vehicle_model_text = tk.StringVar(value = self.settings_dict["Vehicle Model"])
        self.vehicle_model = tk.Entry(self.ecu_frame,textvariable= self.vehicle_model_text, width=24)
        self.vehicle_model.grid(row=3,column=6,sticky=tk.W,padx=5,pady=5)

        tk.Label(self.ecu_frame,text="Vehicle ID (VIN):").grid(row=4,column=0,sticky=tk.W,columnspan=2)
        self.vehicle_vin_text = tk.StringVar(value = self.settings_dict["Vehicle VIN"])
        self.vehicle_vin = tk.Entry(self.ecu_frame, textvariable= self.vehicle_vin_text, width=74)
        self.vehicle_vin.grid(row=4,column=2,sticky=tk.W,padx=5,pady=5,columnspan=6)

        tk.Label(self.ecu_frame,text="ECU Component ID:").grid(row=5,column=0,sticky=tk.W,columnspan=2)
        self.ecu_component_id_text = tk.StringVar(value = self.settings_dict["ECU Component ID"])
        self.ecu_component_id = tk.Entry(self.ecu_frame, textvariable= self.ecu_component_id_text, width=74)
        self.ecu_component_id.grid(row=5,column=2,sticky=tk.W,padx=5,pady=5,columnspan=6)
        #tk.Button(self.ecu_frame,text="Get ID",command=self.get_ecu_software_id).grid(row=5,column=8,sticky=tk.W,padx=5)

        tk.Label(self.ecu_frame,text="ECU Configuration:").grid(row=6,column=0,sticky=tk.W,columnspan=2)
        self.ecu_configuration_text = tk.StringVar(value = self.settings_dict["Engine Configuration"])
        self.ecu_configuration = tk.Entry(self.ecu_frame, textvariable= self.ecu_configuration_text, width=74)
        self.ecu_configuration.grid(row=6,column=2,sticky=tk.W,padx=5,pady=5,columnspan=6)
        
        
        self.sss2_frame = tk.LabelFrame(self.profile_tab, name="sss2_frame",
                                                  text="Smart Sensor Simulator 2 (SSS2) Settings")
        self.sss2_frame.grid(row=1,column=0,sticky=tk.E+tk.W,columnspan=1)

        tk.Label(self.sss2_frame,text="SSS2 Component ID:").grid(row=0,column=0,sticky=tk.W)
        
        self.sss2_serial_number = tk.Entry(self.sss2_frame, name="sss2_serial",textvariable=self.sss_component_id_text,width=75)
        self.sss2_serial_number.grid(row=0,column=1,sticky=tk.W,padx=5,pady=5,columnspan=2)
        self.sss2_serial_number.configure(state='readonly')
        
        #self.sss2_serial_number.insert(0,self.settings_dict["Component ID"])
        self.can_component_id_text = tk.StringVar(value = self.settings_dict["Send SSS2 Component ID"])
        self.can_component_id = ttk.Checkbutton(self.sss2_frame,
                                                text="Send SSS2 Component Information over J1939",
                                                command=self.enable_can_component_id,
                                                variable = self.can_component_id_text,
                                                onvalue="1",
                                                offvalue="0")
        self.can_component_id.grid(row=1,column=1,sticky=tk.W,columnspan=2)
        self.can_component_id.state(['!alternate']) #Clears Check Box
        

        #Uncomment for commissioning
        #tk.Button(self.sss2_frame,text="Set ID",command=self.set_sss2_component_id).grid(row=0,column=8,sticky=tk.W,padx=5)


        tk.Label(self.sss2_frame,text="SSS2 Unique ID:").grid(row=2,column=0,sticky=tk.W)
        self.sss2_product_code_text = tk.StringVar(value = self.settings_dict["SSS2 Product Code"])
        self.sss2_product_code = tk.Entry(self.sss2_frame,textvariable= self.sss2_product_code_text,width=75)
        self.sss2_product_code.grid(row=2,column=1,sticky=tk.W,padx=5,pady=5,columnspan=2)
        #tk.Button(self.sss2_frame,text="Get ID",command=self.get_sss2_unique_id).grid(row=1,column=7,sticky=tk.W)


        tk.Label(self.sss2_frame,text="SSS2 Software ID:").grid(row=3,column=0,sticky=tk.W)
        self.sss_software_id = tk.Entry(self.sss2_frame, textvariable= self.sss_software_id_text,width=75)
        self.sss_software_id.grid(row=3,column=1,sticky=tk.W,padx=5,pady=5,columnspan=2)
        self.sss_software_id.configure(state='readonly')
        #tk.Button(self.sss2_frame,text="Get ID",command=self.get_sss2_software_id).grid(row=2,column=7,sticky=tk.W)

        cable_models = ["SSS2-ADEM2",
                        "SSS2-ADEM3",
                        "SSS2-ADEM4",
                        "SSS2-CM500",
                        "SSS2-CM800",
                        "SSS2-CM2150",
                        "SSS2-CM2250",
                        "SSS2-CM2350",
                        "SSS2-DDEC4",
                        "SSS2-DDEC5",
                        "SSS2-DDEC6",
                        "SSS2-DDEC10",
                        "SSS2-ACM",
                        "SS2-MCM",
                        "SSS2-TCM",
                        "SSS2-MBE",
                        "SSS2-VCU/PLD",
                        "SSS2-MX",
                        "SSS2-MaxxForce",
                        "SSS2-Bendix",
                        "SSS2-BDX-Chassis",
                        "SSS2-Wabco",
                        "SSS2-CUSTOM"]
        tk.Label(self.sss2_frame,text="SSS2 Cable Model:").grid(row=4,column=0,sticky=tk.W)
        self.sss2_cable_text = tk.StringVar(value = self.settings_dict["SSS2 Cable"])
        self.sss2_cable = ttk.Combobox(self.sss2_frame, textvariable= self.sss2_cable_text, values=cable_models)
        self.sss2_cable.grid(row=4,column=1,sticky=tk.W,padx=5,pady=5,columnspan=1)

        self.resisor_box_button_text = tk.StringVar(value = self.settings_dict["Resistor Box Used"])
        self.resisor_box_button = ttk.Checkbutton(self.sss2_frame,text="Supplemental Resistor Box Used",
                                                  offvalue="No",onvalue="Yes",variable=self.resisor_box_button_text)
        self.resisor_box_button.grid(row=4,column=2, padx=5, pady =5,sticky="E")
        self.resisor_box_button.state(['!alternate']) #Clears Check Box
        
        self.file_frame = tk.LabelFrame(self.profile_tab, name="file_frame",
                                                  text="Current Settings Information")
        self.file_frame.grid(row=2,column=0,sticky=tk.N+tk.E+tk.W,columnspan=1)

        tk.Label(self.file_frame,text="Settings File:").grid(row=0,column=0,sticky=tk.E)
        
        self.file_status_label = tk.Label(self.file_frame, textvariable=self.settings_file_status_string,name="file_status_label")
        self.file_status_label.grid(row=0,column=1,sticky=tk.W)
          
        tk.Label(self.file_frame,text="Current SHA-256 Digest:").grid(row=1,column=0,sticky=tk.E)
        self.settings_sha_string = tk.StringVar(name='settings-SHA')
        self.settings_sha_string.set(self.get_settings_hash())
        self.settings_sha_label = tk.Label(self.file_frame, textvariable=self.settings_sha_string,name="settings_sha_label")
        self.settings_sha_label.grid(row=1,column=1,sticky=tk.W,columnspan=3)

        tk.Label(self.file_frame,text="Saved SHA-256 Digest:").grid(row=2,column=0,sticky=tk.E)
        self.file_sha_string = tk.StringVar(name='file-SHA')
        self.file_sha_string.set(self.settings_dict["Original File SHA"])
        self.file_sha_label = tk.Label(self.file_frame, textvariable=self.file_sha_string,name="file_sha_label")
        self.file_sha_label.grid(row=2,column=1,sticky=tk.W,columnspan=3)

        self.version_frame = tk.LabelFrame(self.profile_tab, name="version_frame",
                                                  text="Smart Sensor Simulator Interface Information")
        self.version_frame.grid(row=3,column=0,sticky=tk.S+tk.E+tk.W,columnspan=1)
        self.interface_release = tk.StringVar(value=self.settings_dict["SSS2 Interface Version"])
        tk.Label(self.version_frame,text="File Saved with Smart Sensor Simulator Interface Version:").grid(row=0,column=0,sticky=tk.E)
        tk.Label(self.version_frame, textvariable=self.interface_release).grid(row=0,column=1,sticky=tk.W,columnspan=3)
        self.interface_date = tk.StringVar(value=self.settings_dict["SSS2 Interface Release Date"])
        tk.Label(self.version_frame,text="File Saved with Smart Sensor Simulator Interface Release:").grid(row=1,column=0,sticky=tk.E)
        tk.Label(self.version_frame, textvariable=self.interface_date).grid(row=1,column=1,sticky=tk.W,columnspan=3)
        tk.Label(self.version_frame,text="Current Smart Sensor Simulator Interface Version:").grid(row=2,column=0,sticky=tk.E)
        tk.Label(self.version_frame, text=self.release_version).grid(row=2,column=1,sticky=tk.W,columnspan=3)
        tk.Label(self.version_frame,text="Current Smart Sensor Simulator Interface Release:").grid(row=3,column=0,sticky=tk.E)
        tk.Label(self.version_frame, text=self.release_date).grid(row=3,column=1,sticky=tk.W,columnspan=3)
        

        self.user_frame = tk.LabelFrame(self.profile_tab, name="user_frame",
                                                  text="User Information")
        self.user_frame.grid(row=0,column=1,sticky=tk.N+tk.E+tk.W+tk.S,columnspan=1,rowspan=4)

        tk.Label(self.user_frame,text="Date Loaded:").grid(row=0,column=0,sticky=tk.W,pady=5)
        self.current_date_text = tk.StringVar(value = time.strftime("%A, %d %B %Y %H:%M:%S %Z", time.localtime()))
        self.current_date = tk.Label(self.user_frame, textvariable = self.current_date_text)
        self.current_date.grid(row=0,column=1,sticky=tk.W,padx=5,pady=5)
        
        tk.Label(self.user_frame,text="Date Saved:").grid(row=1,column=0,sticky=tk.W,pady=5)
        self.saved_date_text = tk.StringVar(value = self.settings_dict["Saved Date"])
        self.saved_date = tk.Label(self.user_frame, textvariable = self.saved_date_text)
        self.saved_date.grid(row=1,column=1,sticky=tk.W,padx=5,pady=5)
        
        tk.Label(self.user_frame,text="User Name:").grid(row=2,column=0,sticky=tk.W,pady=5)
        self.user_name_text = tk.StringVar(value = self.settings_dict["Programmed By"])
        self.user_name = tk.Entry(self.user_frame, textvariable=self.user_name_text ,width=60)
        self.user_name.grid(row=2,column=1,sticky=tk.W,padx=5,pady=5)
        
        tk.Label(self.user_frame,text="Company:").grid(row=3,column=0,sticky=tk.W,pady=5)
        self.company_name_text = tk.StringVar(value = self.settings_dict["Company"])
        self.company_name = tk.Entry(self.user_frame, textvariable=self.company_name_text ,width=60)
        self.company_name.grid(row=3,column=1,sticky=tk.W,padx=5,pady=5)

        tk.Label(self.user_frame,text="Location:").grid(row=4,column=0,sticky=tk.W,pady=5)
        self.location_name_text = tk.StringVar(value = self.settings_dict["Location"])
        self.location_name = tk.Entry(self.user_frame, textvariable=self.location_name_text ,width=60)
        self.location_name.grid(row=4,column=1,sticky=tk.W,padx=5,pady=5)
        
        tk.Label(self.user_frame,text="Case Number:").grid(row=5,column=0,sticky=tk.W,pady=5)
        self.case_number_text = tk.StringVar(value = self.settings_dict["Case Number"])
        self.case_number = tk.Entry(self.user_frame, textvariable=self.case_number_text ,width=60)
        self.case_number.grid(row=5,column=1,sticky=tk.W,padx=5,pady=5)
        
        tk.Label(self.user_frame,text="Date:").grid(row=6,column=0,sticky=tk.W,pady=5)
        self.date_of_loss_text = tk.StringVar(value = self.settings_dict["Date of Loss"])
        self.date_of_loss = tk.Entry(self.user_frame, textvariable=self.date_of_loss_text ,width=60)
        self.date_of_loss.grid(row=6,column=1,sticky=tk.W,padx=5)
       
        tk.Label(self.user_frame,text="User Notes:").grid(row=7,column=0,sticky=tk.W)
        self.case_notes = tkst.ScrolledText(self.user_frame, height=18,width=53,padx=5,pady=4,wrap=tk.WORD)
        self.case_notes.grid(row=8,column=0,sticky=tk.W,padx=5,pady=5,columnspan=2)
        self.case_notes.focus_set()
        self.case_notes.insert(1.0,self.settings_dict["User Notes"].strip())
        
        self.warning_frame = tk.LabelFrame(self.profile_tab, name="warning_frame",
                                                  text="Warnings and Cautions")
        self.warning_frame.grid(row=4,column=0,sticky=tk.N+tk.E+tk.W,columnspan=2,rowspan=1)
        self.warning_text = tk.Text(self.warning_frame,height=3,wrap=tk.WORD,width=130)
        self.warning_text.grid(row=0,column=0,sticky=tk.E+tk.W,padx=5,pady=5)
        self.warning_text.insert(tk.END,self.settings_dict["Warnings"])
        self.warning_text.configure(state='disabled')
        
        logo_file = tk.PhotoImage(file="SynerconLogoWithName.gif")
        logo = tk.Label(self.profile_tab,image=logo_file)
        logo.image= logo_file
        logo.grid(row=0,column=2,sticky=tk.W)
        logo.bind("<Button-1>", self.open_link)
        
        link = tk.Label(self.profile_tab, text="Visit: http://www.synercontechnologies.com/SSS2/", fg="blue", cursor="hand2")
        link.grid(row=4,column=2,sticky=tk.S)
        link.bind("<Button-1>", self.open_link)

        angled_photo = tk.PhotoImage(file="sss2angle.gif")
        new_photo = angled_photo.subsample(2,2)
        
        image_label = Label(self.profile_tab,image=new_photo)
        image_label.image = new_photo
        image_label.grid(row=1,column=2,sticky="NE",rowspan=2)       
        
        button_frame = tk.Frame(self.profile_tab)
        button_frame.grid(row=3,column=2,rowspan=2)
        tk.Button(button_frame,text="Open Settings File",command=self.open_settings_file,width = 50).grid(row=0,column=0,pady=2)
        tk.Button(button_frame,text="Save Settings File",command=self.save_settings_file,width = 50).grid(row=1,column=0,pady=2)
        tk.Button(button_frame,text="Save Settings File As...",command=self.saveas_settings_file,width = 50).grid(row=2,column=0,pady=2)
        tk.Button(button_frame,text="Get SSS2 Unique ID",command=self.get_sss2_unique_id,width = 50).grid(row=3,column=0,pady=2)
        
    def open_link(self,event=None):
        webbrowser.open_new(r"http://www.synercontechnologies.com/SSS2/")
        
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
        commandString = "CI,{}".format(self.sss2_serial_number.get())
        self.tx_queue.put_nowait(commandString)

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
                    pot["Wire Color"] =         pot_object.ecu_app.ecu_color.get()
                    pot["Application"] =        pot_object.ecu_app.ecu_app.get()

        for dac_key in self.dac_objects.keys():
            dac_dict=self.settings_dict["DACs"][dac_key]
            dac_dict["Average Voltage"] = self.dac_objects[dac_key].dac_mean_slider.get()/100
            dac_dict["ECU Pins"] =        self.dac_objects[dac_key].ecu_app.ecu_pins.get()
            dac_dict["Wire Color"] =        self.dac_objects[dac_key].ecu_app.ecu_color.get()
            dac_dict["Application"] =     self.dac_objects[dac_key].ecu_app.ecu_app.get()

        for pwm_key in self.pwm_objects.keys():
            pwm_dict=self.settings_dict["PWMs"][pwm_key]
            pwm_dict["Duty Cycle"] = self.pwm_objects[pwm_key].pwm_duty_cycle_slider.get()
            pwm_dict["Frequency"] = self.pwm_objects[pwm_key].pwm_frequency_slider.get()
            pwm_dict["ECU Pins"] =        self.pwm_objects[pwm_key].ecu_app.ecu_pins.get()
            pwm_dict["Wire Color"] =        self.pwm_objects[pwm_key].ecu_app.ecu_color.get()
            pwm_dict["Application"] =     self.pwm_objects[pwm_key].ecu_app.ecu_app.get()

        hv_dict=self.settings_dict["HVAdjOut"]
        hv_dict["Average Voltage"] = self.hvadjout.dac_mean_slider.get()/100
        hv_dict["ECU Pins"] =        self.hvadjout.ecu_app.ecu_pins.get()
        hv_dict["Wire Color"] =        self.hvadjout.ecu_app.ecu_color.get()
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
        s["CAN1 Connect"]["State"]=self.can1_switch.switch_button.instate(['selected'])
        s["PWM5 Connect"]["State"]=self.pwm5_switch.switch_button.instate(['selected'])
        s["PWM6 Connect"]["State"]=self.pwm6_switch.switch_button.instate(['selected'])
        s["PWM4_28 Connect"]["State"]=self.pwm4_28_switch.switch_button.instate(['selected'])

        self.settings_dict["ECU Year"] = self.ecu_year_text.get()
        self.settings_dict["ECU Make"] = self.ecu_make_text.get()
        self.settings_dict["ECU Model"] = self.ecu_model_text.get()
        self.settings_dict["ECU Software Version"] = self.sss_ecu_id_text.get()
        self.settings_dict["Engine Serial Number"] = self.engine_serial_text.get()
        self.settings_dict["Vehicle Year"] = self.vehicle_year_text.get()
        self.settings_dict["Vehicle Make"] = self.vehicle_make_text.get()
        self.settings_dict["Vehicle Model"] = self.vehicle_model_text.get()
        self.settings_dict["Engine Configuration"] = self.ecu_configuration_text.get()
        self.settings_dict["Component ID"] = self.sss_component_id_text.get()
        self.settings_dict["Send SSS2 Component ID"] = self.can_component_id_text.get()
        self.settings_dict["SSS2 Product Code"] = self.sss2_product_code_text.get()
        self.settings_dict["Software ID"] = self.sss_software_id_text.get()
        self.settings_dict["SSS2 Cable"] = self.sss2_cable_text.get()
        self.settings_dict["Resistor Box Used"] = self.resisor_box_button_text.get()
        self.settings_dict["Saved Date"] = self.saved_date_text.get()
        self.settings_dict["Serial Number"] = self.sss2_serial_number.get() 
        self.settings_dict["Vehicle VIN"] = self.vehicle_vin_text.get().strip()
        self.settings_dict["ECU Component ID"] = self.ecu_component_id_text.get()
        self.settings_dict["Original Creation Date"]=self.current_date_text.get()
        self.settings_dict["Programmed By"] = self.user_name_text.get()
        self.settings_dict["Company"] = self.company_name_text.get()
        self.settings_dict["Location"] = self.location_name_text.get()
        self.settings_dict["Case Number"] = self.case_number_text.get()
        self.settings_dict["Date of Loss"] = self.date_of_loss_text.get()
        self.settings_dict["User Notes"] = self.case_notes.get(1.0,tk.END).strip()
        try:
            self.settings_dict["File Name"] = os.path.basename(self.filename)
        except:
            pass

        self.settings_dict["CAN Config"]["CAN0 Baudrate"] = self.j1939_baud.get()
        self.settings_dict["CAN Config"]["CAN1 Baudrate"] = self.can2_baud.get()
        self.settings_dict["CAN Config"]["MCPCAN Baudrate"] = self.can1_baud.get()

        self.settings_dict["SSS2 Interface Release Date"] = self.release_date
        self.settings_dict["SSS2 Interface Version"] = self.release_version

        
        
    def get_all_children(self,tree, item=""):
        children = tree.get_children(item)
        for child in children:
            children += self.get_all_children(tree, child)
        return children
    def send_transmit_can(self):
        commandString = "STARTCAN,"
        for tree_item in self.get_all_children(self.can_tree):
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
        #self.tx_queue.put_nowait("CLEARCAN,")

    def send_reload_can(self):
        msg_index=0
        for msgKey in self.settings_dict["CAN"]:
            self.load_can_frame(self.settings_dict["CAN"][msgKey])
            time.sleep(0.002)
            msg_index+=1
        self.tx_queue.put_nowait("RELOAD,")

    def send_j1939_baud(self):
        commandString = "B0,{}".format(self.j1939_baud_value.get())
        self.tx_queue.put_nowait(commandString)
        
    def send_can2_baud(self):
        self.tx_queue.put_nowait("B1,{}".format(self.can2_baud_value.get()))

    def send_can1_baud(self):
        self.tx_queue.put_nowait("BMCP,{}".format(self.can1_baud_value.get()))
        
    def vehicle_networks_settings(self):

        self.truck_networks_tab.grid_rowconfigure(5,weight=2) #Expands blank space under radio buttons.
        self.truck_networks_tab.grid_columnconfigure(3,weight=1) #Expands blank space 
        self.truck_networks_tab.grid_columnconfigure(4,weight=2) #Expands blank space 


        ttk.Button(self.truck_networks_tab,
                                    text="Transmit all CAN messages", width = 35,
                                    command=self.send_transmit_can).grid(row=0,
                                                                         column=1,
                                                                         sticky="W",columnspan=3,
                                                                         pady=5,padx=5)
        
        ttk.Button(self.truck_networks_tab, width = 35,
                                    text="Stop Sending all CAN messages",
                                    command=self.send_stop_can).grid(row=1,
                                                                     column=1,
                                                                     sticky="W",columnspan=3,
                                                                     pady=5,padx=5)
        
        tk.Label(self.truck_networks_tab,text="J1939 Bit Rate:").grid(row=2,column=1,sticky="E")
        
        self.j1939_baud = ttk.Combobox(self.truck_networks_tab,
                                   textvariable=self.j1939_baud_value,
                                   width=8,
                                   values=self.baudrates)
        self.j1939_baud.set(self.settings_dict["CAN Config"]["CAN0 Baudrate"])
        self.j1939_baud.grid(row=2,column=2,sticky="W",pady=5,columnspan=1)
        ttk.Button(self.truck_networks_tab, width = 9,
                                    text="Set",command=self.send_j1939_baud).grid(row=2,
                                                                     column=3,
                                                                     sticky="W",columnspan=1,
                                                                     pady=5,padx=5)
        self.send_j1939_baud()
        

        tk.Label(self.truck_networks_tab,text="CAN1 Bit Rate:").grid(row=3,column=1,sticky="E")
        
        self.can1_baud = ttk.Combobox(self.truck_networks_tab,
                                   textvariable=self.can1_baud_value,
                                   width=8,
                                   values=self.baudrates)
        self.can1_baud.set(self.settings_dict["CAN Config"]["MCPCAN Baudrate"])
        self.can1_baud.grid(row=3,column=2,sticky="W",pady=5,columnspan=1)
        ttk.Button(self.truck_networks_tab, width = 9,
                                    text="Set",command=self.send_can1_baud).grid(row=3,
                                                                     column=3,
                                                                     sticky="W",columnspan=1,
                                                                     pady=5,padx=5)
        self.send_can1_baud()

        tk.Label(self.truck_networks_tab,text="CAN2 Bit Rate:").grid(row=4,column=1,sticky="E")
        
        self.can2_baud = ttk.Combobox(self.truck_networks_tab,
                                   textvariable=self.can2_baud_value,
                                   width=8,
                                   values=self.baudrates)
        self.can2_baud.set(self.settings_dict["CAN Config"]["CAN1 Baudrate"])
        self.can2_baud.grid(row=4,column=2,sticky="W",pady=5,columnspan=1)
        ttk.Button(self.truck_networks_tab, width = 9,
                                    text="Set",command=self.send_can2_baud).grid(row=4,
                                                                     column=3,
                                                                     sticky="W",columnspan=1,
                                                                     pady=5,padx=5)
        self.send_can2_baud()
        
        logo_file = tk.PhotoImage(file="SynerconLogoWithName300.gif")
        logo = tk.Label(self.truck_networks_tab,image=logo_file)
        logo.image= logo_file
        logo.grid(row=0,column=4,sticky=tk.E,rowspan=5)
        
        self.can_edit_frame = tk.LabelFrame(self.truck_networks_tab, name="edit_can",text="CAN Message Editor")
        self.can_edit_frame.grid(row=5,column=1,sticky="EW",columnspan=4,rowspan=1)
        
        tk.Label(self.can_edit_frame,text="Description:").grid(row=0,column=0,sticky="E")
        self.can_name_value = tk.StringVar()
        self.can_name = ttk.Entry(self.can_edit_frame,textvariable=self.can_name_value,width=65)
        self.can_name.grid(row=0,column=1,sticky="W",columnspan=6,pady=5)
        #self.can_name.bind('<Return>',self.modify_can_message)
        #self.can_name.bind('<Tab>',self.modify_can_message)
        

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
        self.can_sub = tk.Label(self.can_edit_frame,textvariable=self.can_sub_value,width=10)
        self.can_sub.grid(row=1,column=5,sticky="W",pady=5,columnspan=1)

        
        tk.Label(self.can_edit_frame,text="Hex CAN ID:").grid(row=2,column=0,sticky="E")
        self.can_id_value=tk.StringVar()
        self.can_id = tk.Entry(self.can_edit_frame,textvariable=self.can_id_value,width=12)
        self.can_id.grid(row=2,column=1,sticky="W",pady=5,columnspan=2)
        self.can_name.bind('<Return>',self.modify_can_message)
        self.can_name.bind('<Tab>',self.modify_can_message)
        


        tk.Label(self.can_edit_frame,text="DLC:").grid(row=2,column=2,sticky="E")
        self.can_dlc_value=tk.StringVar(value="8")
        spinbox_values = ["1","2","3","4","5","6","7","8"]
        self.can_dlc = ttk.Combobox(self.can_edit_frame,textvariable=self.can_dlc_value,width=2,values=spinbox_values)
        self.can_dlc.grid(row=2,column=3,sticky="W",pady=5,columnspan=1)
        self.can_dlc.bind('<<ComboboxSelected>>',self.modify_can_message)
       

        
        self.can_ext_id_state = tk.IntVar(value=1)
        self.can_ext_id = ttk.Checkbutton(self.can_edit_frame,text="Use Extended (29-bit) ID",
                                          variable=self.can_ext_id_state,
                                          command=self.modify_can_message)
        self.can_ext_id.grid(row=2,column=4,sticky="W",padx=10,columnspan=3)
        
        tk.Label(self.can_edit_frame,text="Channel:").grid(row=3,column=0,sticky="E")
        self.can_radio_frame = tk.Frame(self.can_edit_frame)
        self.can_radio_frame.grid(row=3,column=1,sticky="W",columnspan=2,pady=5)
        self.can_channel_value = tk.StringVar(value="0")
        self.can_channel_0 = ttk.Radiobutton(self.can_radio_frame,value="0",text="J1939",variable=self.can_channel_value,
                                        command=self.modify_can_message)
        self.can_channel_0.grid(row=0,column=0,sticky="E")
        self.can_channel_0 = ttk.Radiobutton(self.can_radio_frame,value="2",text="CAN1",variable=self.can_channel_value,
                                        command=self.modify_can_message)
        self.can_channel_0.grid(row=0,column=1,sticky="W")
        self.can_channel_0 = ttk.Radiobutton(self.can_radio_frame,value="1",text="CAN2",variable=self.can_channel_value,
                                        command=self.modify_can_message)
        self.can_channel_0.grid(row=0,column=2,sticky="W")
        
        self.can_send_state = tk.IntVar(value=1)
        self.can_send = ttk.Checkbutton(self.can_edit_frame,
                                        text="Enable Transmission (Send)",
                                        variable=self.can_send_state,
                                        command=self.modify_can_message)
        self.can_send.grid(row=3,column=4,sticky="W",padx=10,columnspan=3)
        
        tk.Label(self.can_edit_frame,text="Period (msec):").grid(row=4,column=0,sticky="E")
        self.can_period_value = tk.StringVar(value="100")
        self.can_period = tk.Entry(self.can_edit_frame,textvariable=self.can_period_value,width=10)
        self.can_period.grid(row=4,column=1,sticky="W",pady=5)
        self.can_period.bind('<Return>',self.modify_can_message)
        self.can_period.bind('<Tab>',self.modify_can_message)
        


        tk.Label(self.can_edit_frame,text="  Restart (msec):").grid(row=4,column=2,sticky="E")
        self.can_restart_value = tk.StringVar(value="0")
        self.can_restart = tk.Entry(self.can_edit_frame,textvariable=self.can_restart_value,width=10)
        self.can_restart.grid(row=4,column=3,sticky="W",pady=5)
        self.can_restart.bind('<Return>',self.modify_can_message)
        self.can_restart.bind('<Tab>',self.modify_can_message)
        

        tk.Label(self.can_edit_frame,text="Total to Send:").grid(row=4,column=4,sticky="E")
        self.can_total_value = tk.StringVar(value="0")
        self.can_total = tk.Entry(self.can_edit_frame,textvariable=self.can_total_value,width=10)
        self.can_total.grid(row=4,column=5,sticky="W")
        self.can_total.bind('<Return>',self.modify_can_message)
        self.can_total.bind('<Tab>',self.modify_can_message)
        
        self.can_data_frame = tk.Frame(self.can_edit_frame)
        self.can_byte_value=[]
        self.can_byte=[]
        for byteLabel in range(8):
            tk.Label(self.can_data_frame,text=" B{}:".format(byteLabel+1)).grid(row=0,column=2*byteLabel)
            self.can_byte_value.append(tk.StringVar(value="00"))
            self.can_byte.append(tk.Entry(self.can_data_frame,textvariable=self.can_byte_value[byteLabel],width=3))
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

        colWidths = [50,50,50,50,55,50,50,50,30,75,35,24,24,24,24,24,24,24,24]
        self.colNames = ["Thread","Count","Index","Send","Channel","Period","Restart","Total","Ext","CAN HEX ID","DLC","B1","B2","B3","B4","B5","B6","B7","B8"]
        colPos = ['center','center','center','center','center',tk.E,tk.E,tk.E,'center',tk.E,'center','center','center','center',
                  'center','center','center','center','center','center']
        self.display_cols = ["Send","Channel","Period","Restart","Total","Ext","CAN HEX ID","DLC","B1","B2","B3","B4","B5","B6","B7","B8"]
        self.can_tree = ttk.Treeview(self.can0_frame, selectmode = "browse",
                                     displaycolumns="#all",columns = self.colNames,height=31)
        
        self.can_tree.grid(row=0,column=0)

        self.can_tree.heading("#0", anchor = tk.W, text = "Label")
        for c,w,p in zip(self.colNames,colWidths,colPos):
            self.can_tree.column(c, anchor = p, stretch = False, width = w)
            self.can_tree.heading(c, anchor = p, text = c)
        self.item_identifier={}

        self.send_clear_can()
        for i in self.can_tree.get_children():
            self.can_tree.delete(i)
        self.new_message = True
        for msg_index in sorted(self.settings_dict["CAN"].keys()):
            self.load_can_frame(self.settings_dict["CAN"][msg_index])
            time.sleep(0.005)

            
        
        self.can_tree.bind('<<TreeviewSelect>>',self.fill_can_box)

            
        self.message_config_frame = tk.LabelFrame(self.truck_networks_tab, name="network Configurations",
                                                  text="Network Configurations")
        self.message_config_frame.grid(row=6,column=1,sticky="EW",columnspan=4)

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
        self.send_single_frame()
        
    def delete_can_message(self):
        selection = self.can_tree.selection()
        can_msg = self.can_tree.item(selection)
        index = self.can_thread_value.get()
        sub = self.can_sub_value.get()
        commandString = "GO,{},0".format(index) 
        self.tx_queue.put_nowait(commandString)
        del self.settings_dict["CAN"]["{:>3d}.{:03d}".format(int(index),int(sub))] 
        for tree_item in self.can_tree.get_children(selection):
            self.can_tree.delete(tree_item)
        prev_selection = self.can_tree.prev(selection)
        self.can_tree.delete(selection)
        self.can_tree.selection_set(prev_selection)

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
        elif self.can_channel_value.get() == "2":
            chan = "CAN1"
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
            elif self.can_channel_value.get() == "2":
                chan = "CAN1"
            elif self.can_channel_value.get() == "1":
                chan = "CAN2"
            self.can_tree.set(tree_item,"Channel",chan)
            self.can_tree.set(tree_item,"Period",self.can_period_value.get())
            self.can_tree.set(tree_item,"Restart",self.can_restart_value.get())
            self.can_tree.set(tree_item,"Total",self.can_total_value.get())
            self.can_tree.set(tree_item,"DLC",self.can_dlc_value.get())
            
                     
    def create_new_message(self):
        new_name = simpledialog.askstring("Input", "New CAN Message Name:",parent=self, initialvalue="CAN Message")
        if new_name is None:
            return
        self.new_message = True
        self.can_name_value.set(new_name)
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
        selection = self.can_tree.selection()
        can_msg = self.can_tree.item(selection)
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
        try:
            m += ",{},".format(abs(int(self.can_period_value.get())))
            self.can_period['bg']='white'
        except Exception as e:
            print(e)
            self.root.bell()
            self.can_period.focus()
            self.can_period['bg']='yellow'
            return
        
        try:
            m += "{},".format(abs(int(self.can_restart_value.get())))
            self.can_restart['bg']='white'
        except Exception as e:
            print(e)
            self.root.bell()
            self.can_restart.focus()
            self.can_restart['bg']='yellow'
            return

        try:
            m += "{},".format(abs(int(self.can_total_value.get())))
            self.can_total['bg']='white'
        except Exception as e:
            print(e)
            self.root.bell()
            self.can_total.focus()
            self.can_total['bg']='yellow'
            return
        
        m += str(self.can_ext_id_state.get())
        m += ","
        try:
            if self.can_ext_id_state.get() == 1:
                m += "{:>8X},".format(int(self.can_id_value.get(),16) & 0x1FFFFFFF)
            else:
                m += "{:>3X},".format(int(self.can_id_value.get(),16) & 0x7FF)
            self.can_id['bg']='white'
        except Exception as e:
            print(e)
            self.root.bell()
            self.can_id.focus()
            self.can_id['bg']='yellow'
            return
        
        try:
            m += "{},".format(abs(int(self.can_dlc_value.get()) & 0x0F))
            self.can_dlc['background']='white'
        except Exception as e:
            print(e)
            self.root.bell()
            self.can_dlc.focus()
            self.can_dlc['background']='yellow'
            return

        for i in range(8):
            try:
                m += "{:02X},".format(abs(int(self.can_byte_value[i].get(),16) & 0xFF))
                self.can_byte[i]['bg']='white'
            except Exception as e:
                print(e)
                self.root.bell()
                self.can_byte[i].focus()
                self.can_byte[i]['bg']='yellow'
                return
        
        if self.can_send_state.get() == 1:
            m += "Yes"
        else:
            m += "No"
        
        self.load_can_frame(m)
        
    def send_single_frame(self,event=None):
        commandString = "GO,{},{}".format(self.can_thread_value.get(),self.can_send_state.get()) 
        self.tx_queue.put_nowait(commandString)

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
            if vals[4] == "CAN1":
                self.can_channel_value.set("2")
            elif vals[4] == "CAN2":
                self.can_channel_value.set("1")
            else:
                self.can_channel_value.set("0")
            self.can_period_value.set(vals[5])
            self.can_restart_value.set(vals[6])
            self.can_total_value.set(vals[7])
            for i in range(8):
                self.can_byte_value[i].set(vals[11+i])
            self.modify_can_button.configure(state=tk.NORMAL)
        else:
            self.modify_can_button.configure(state=tk.DISABLED)

    def load_can_frame(self,message_string):
        
        msg = message_string.split(',')
        msgKey = msg[0].strip()
        index = msg[1].strip()
        
        num = msg[2].strip()
        sub = msg[3].strip()

        #Switch CAN 1 and 2 becuse they are switched on the Arduino
        if msg[4] == "0":
            channel = "J1939"
        elif msg[4] == "2":
            channel = "CAN1"
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
            msg_iid = self.find_next_iid()
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
            try:
                selection = int(selection[0])
            except:
                pass

        self.can_tree.selection_set(selection)
         
         

        self.can_thread_value.set(index)
        if send == "Yes":
            self.can_send_state.set(1)
        else:
            self.can_send_state.set(0)

        self.send_single_frame()
        self.settings_dict["CAN"]["{:>3d}.{:03d}".format(int(index),int(sub))] = message_string 
        commandString = "SM,"+message_string
        self.tx_queue.put_nowait(commandString)   
        
    def find_next_iid(self):
        iid_list=[0]
        for tree_item in self.get_all_children(self.can_tree):
            #print(tree_item)
            try:
                iid_list.append(int(tree_item))
            except:
                iid_list.append(0)
        
        return max(iid_list) + 1
        
    def voltage_out_settings(self):
       
        self.DAC_bank = tk.LabelFrame(self.voltage_out_tab, name="dac_bank",
                                                  text="Voltage Outputs")
        self.DAC_bank.grid(row=2,column=0,sticky="NW",columnspan=1)
        self.DAC_bank.grid_rowconfigure(4,weight=2) #Expands blank space under radio buttons.

        dac_dict=self.settings_dict["DACs"]
        self.dac_objects={}
        for key,c,r in zip(sorted(dac_dict.keys()),[0,1,2,3,0,1,2,3],[0,0,0,0,1,1,1,1]):
            self.dac_objects[key] = DAC7678(self.DAC_bank,self.tx_queue, dac_dict[key], row=r, col=c)
        
        self.vout2a_switch = config_radio_switches(self.DAC_bank,self.tx_queue,
                            self.settings_dict["Switches"],"Port 10 or 19",rowA=2,colA=1,rowB=3,colB=1)
        self.vout2b_switch = config_radio_switches(self.DAC_bank,self.tx_queue,
                            self.settings_dict["Switches"],"Port 15 or 18",rowA=2,colA=0,rowB=3,colB=0)
        
        self.hvadjout_bank = tk.LabelFrame(self.extra_tab, name="hvadjout_bank",
                                                  text="High Current Adjustable Regulator")
        self.hvadjout_bank.grid(row=2,column=2,sticky="SW",columnspan=1,rowspan=1)
        self.hvadjout = DAC7678(self.hvadjout_bank,self.tx_queue,
                                self.settings_dict["HVAdjOut"],
                                row=0,
                                col=0,
                                software_ID = self.sss_software_id_text)

        self.extra_tab.grid_rowconfigure(3,weight=2)                                         
        logo_file = tk.PhotoImage(file="SSS2Pins.gif")
        logo = tk.Label(self.extra_tab,image=logo_file)
        logo.image= logo_file
        logo.grid(row=3,column=2,sticky="SW",columnspan=3,rowspan=1)

        logo_file = tk.PhotoImage(file="SynerconLogoWithName300.gif")
        logo = tk.Label(self.extra_tab,image=logo_file)
        logo.image= logo_file
        logo.grid(row=0,column=3,sticky=tk.W,columnspan=2,rowspan=2)
        

        tk.Label(self.voltage_out_tab,text="The following share a common frequency: PWM1 and PWM2,  PWM3 and PWM4, PWM5 and PWM6. Adjusting one in the group will affect the other.").grid(row=1,column=0)
        self.pwm_bank=tk.LabelFrame(self.voltage_out_tab, name="pwm_bank",
                                                  text="Pulse Width Modulated (PWM) Outputs")
        self.pwm_bank.grid(row=0,column=0,sticky="SE",columnspan=1)

        self.pwm1_switch = config_switches(self.pwm_bank,self.tx_queue,
                            self.settings_dict["Switches"],"PWM1 Connect",row=1,col=0)
        self.pwm2_switch = config_switches(self.pwm_bank,self.tx_queue,
                            self.settings_dict["Switches"],"PWM2 Connect",row=1,col=1)
        self.pwm3_switch = config_radio_switches(self.pwm_bank,self.tx_queue,
                            self.settings_dict["Switches"],"PWM3 or 12V",rowA=1,colA=2,rowB=2,colB=2)
        
        self.pwm4_switch = config_radio_switches(self.pwm_bank,self.tx_queue,
                            self.settings_dict["Switches"],"PWM4 or Ground",rowA=1,colA=3,rowB=2,colB=3)
        self.pwm4_28_switch = config_switches(self.pwm_bank,self.tx_queue,
                            self.settings_dict["Switches"],"PWM4_28 Connect",row=3,col=3)
        self.pwm5_switch = config_switches(self.pwm_bank,self.tx_queue,
                            self.settings_dict["Switches"],"PWM5 Connect",row=1,col=4)
        self.pwm6_switch = config_switches(self.pwm_bank,self.tx_queue,
                            self.settings_dict["Switches"],"PWM6 Connect",row=1,col=5)
                
        self.pwm12_switch = config_radio_switches(self.pwm_bank,self.tx_queue,
                            self.settings_dict["Switches"],"PWMs or CAN2",rowA=2,colA=0,rowB=3,colB=0)
        self.pwm_objects={}
        pwm_dict=self.settings_dict["PWMs"]
        col_index=0
        for key in sorted(pwm_dict.keys()):
            self.pwm_objects[key] = pwm_out(self.pwm_bank,self.tx_queue, pwm_dict[key], row=0, col=col_index)
            col_index+=1
            
    def data_logger(self):


        self.can1_switch = config_switches(self.data_logger_tab,self.tx_queue,
                            self.settings_dict["Switches"],"CAN1 Connect",row=2,col=1)
        
        self.data_logger_tab.grid_columnconfigure(3,weight=2) #Expands blank space 

        buffer_size_frame = tk.Frame(self.data_logger_tab)
        tk.Label(buffer_size_frame,text="Buffer Size:").grid(row=0,column=0,sticky=tk.E)
        self.j1939_size_value = tk.StringVar(value = 1000000)
        self.j1939_size = tk.Entry(buffer_size_frame,textvariable= self.j1939_size_value, width=10)
        self.j1939_size.grid(row=0,column=1,sticky=tk.W,padx=5,pady=2)
        buffer_size_frame.grid(row=0,column=0,sticky=tk.W)
        warning= tk.Label(self.data_logger_tab,
                          text= "Caution: Using the datalogger features can set fault codes. CAN messages may be faster than USB and messages may be dropped. ",
                          background = "yellow",justify=tk.CENTER,relief=tk.RAISED)
        warning.grid(row=0,column=1,columnspan=2,sticky="EW")
        
        self.j1939_frame = tk.LabelFrame(self.data_logger_tab, text="J1939 Messages")
        self.j1939_frame.grid(row=1,column=0,sticky='NSEW')

        tk.Label(self.j1939_frame,text="J1939 Bit Rate:").grid(row=1,column=0,sticky="E")
        self.j1939_baud = ttk.Combobox(self.j1939_frame,
                                   textvariable=self.j1939_baud_value,
                                   width=8,
                                   values=self.baudrates)
        self.j1939_baud.grid(row=1,column=1,sticky="W",pady=5,columnspan=1)
        ttk.Button(self.j1939_frame, width = 9,
                                    text="Set",command=self.send_j1939_baud).grid(row=1,
                                                                     column=2,
                                                                     sticky="W",columnspan=1,
                                                                     pady=5,padx=5)
        

        self.stream_can0_box =  ttk.Checkbutton(self.j1939_frame,
                                    text="Stream CAN0 (J1939)",
                                    command=self.send_stream_can0)
        self.stream_can0_box.grid(row=0,column=0,sticky="W")
        self.stream_can0_box.state(['!alternate']) #Clears Check Box

        tk.Button(self.j1939_frame,text="Clear Buffer", command=self.clear_j1939_buffer).grid(row=0,column=1,pady=5,sticky=tk.N+tk.W)
        tk.Button(self.j1939_frame,text="Save Buffer", command=self.save_j1939_buffer).grid(row=0,column=2,pady=5,sticky=tk.N+tk.W)
        tk.Button(self.j1939_frame,text="Save Buffer As...", command=self.save_j1939_buffer_as).grid(row=0,column=3,pady=5,sticky=tk.N+tk.W)
    
        
        colWidths = [60,30,24,24,24,24,24,24,24,24,50]
        colNames = ["Period","DLC","B0","B1","B2","B3","B4","B5","B6","B7","Count"]
        colPos = ['center','center','center','center','center','center','center','center','center','center','center']
        
        self.j1939_tree = ttk.Treeview(self.j1939_frame, selectmode = "browse",columns=colNames, displaycolumns="#all", height=25)
        self.j1939_tree.heading("#0", anchor = tk.E, text = "CAN ID")
        self.j1939_tree.column("#0",width=75)
        for c,w,p in zip(colNames,colWidths,colPos):
            self.j1939_tree.column(c, anchor = p, stretch = False, width = w)
            self.j1939_tree.heading(c, anchor = p, text = c)
        self.j1939_tree.grid(row=2,column=0,columnspan=4)
        self.j1939_frame.columnconfigure(3, weight=1)
        self.j1939_frame.rowconfigure(2, weight=1)
        
        self.j1939_unique_messages = {}
        self.j1939_prior_messages = {}

        self.can1_frame = tk.LabelFrame(self.data_logger_tab, text="CAN1 Messages")
        self.can1_frame.grid(row=1,column=1,sticky='NSEW')

        tk.Label(self.can1_frame,text="CAN1 Bit Rate:").grid(row=1,column=0,sticky="E")
        self.can1_baud = ttk.Combobox(self.can1_frame,
                                   textvariable=self.can1_baud_value,
                                   width=8,
                                   values=self.baudrates)
        self.can1_baud.grid(row=1,column=1,sticky="W",pady=5,columnspan=1)
        ttk.Button(self.can1_frame, width = 9,
                                    text="Set",command=self.send_can1_baud).grid(row=1,
                                                                     column=2,
                                                                     sticky="W",columnspan=1,
                                                                     pady=5,padx=5)

        self.stream_can1_box =  ttk.Checkbutton(self.can1_frame,
                                    name="stream CAN1 (MCPCAN)",
                                    text="Stream CAN1 (MCPCAN)",
                                    command=self.send_stream_can1)
        self.stream_can1_box.grid(row=0,column=0,sticky="W")
        self.stream_can1_box.state(['!alternate']) #Clears Check Box

        tk.Button(self.can1_frame,text="Clear Buffer", command=self.clear_can1_buffer).grid(row=0,column=1,pady=5,sticky=tk.N+tk.W)
        tk.Button(self.can1_frame,text="Save Buffer", command=self.save_can1_buffer).grid(row=0,column=2,pady=5,sticky=tk.N+tk.W)
        tk.Button(self.can1_frame,text="Save Buffer As...", command=self.save_can1_buffer_as).grid(row=0,column=3,pady=5,sticky=tk.N+tk.W)
    
        self.can1_tree = ttk.Treeview(self.can1_frame, selectmode = "browse",columns=colNames, displaycolumns="#all", height=25)
        self.can1_tree.heading("#0", anchor = tk.E, text = "CAN ID")
        self.can1_tree.column("#0",width=75)
        for c,w,p in zip(colNames,colWidths,colPos):
            self.can1_tree.column(c, anchor = p, stretch = False, width = w)
            self.can1_tree.heading(c, anchor = p, text = c)
        self.can1_tree.grid(row=2,column=0,columnspan=4,sticky=tk.S+tk.W)
        self.can1_frame.columnconfigure(3, weight=1)
        self.can1_frame.rowconfigure(2, weight=1)
        self.can1_unique_messages = {}
        self.can1_prior_messages = {}


        self.can2_frame = tk.LabelFrame(self.data_logger_tab, text="CAN2 Messages")
        self.can2_frame.grid(row=1,column=2,sticky='NSEW')

        tk.Label(self.can2_frame,text="CAN2 Bit Rate:").grid(row=1,column=0,sticky="E")
        self.can2_baud = ttk.Combobox(self.can2_frame,
                                   textvariable=self.can2_baud_value,
                                   width=8,
                                   values=self.baudrates)
        self.can2_baud.grid(row=1,column=1,sticky="W",pady=5,columnspan=1)
        ttk.Button(self.can2_frame, width = 9,
                                    text="Set",command=self.send_can2_baud).grid(row=1,
                                                                     column=2,
                                                                     sticky="W",columnspan=1,
                                                                     pady=5,padx=5)

        self.stream_can2_box =  ttk.Checkbutton(self.can2_frame,
                                    name="stream CAN2 (E-CAN)",
                                    text="Stream CAN2 (PTCAN)",
                                    command=self.send_stream_can2)
        self.stream_can2_box.grid(row=0,column=0,sticky="W")
        self.stream_can2_box.state(['!alternate']) #Clears Check Box

        tk.Button(self.can2_frame,text="Clear Buffer", command=self.clear_can2_buffer).grid(row=0,column=1,pady=5,sticky=tk.N+tk.W)
        tk.Button(self.can2_frame,text="Save Buffer", command=self.save_can2_buffer).grid(row=0,column=2,pady=5,sticky=tk.N+tk.W)
        tk.Button(self.can2_frame,text="Save Buffer As...", command=self.save_can2_buffer_as).grid(row=0,column=3,pady=5,sticky=tk.N+tk.W)
    
        self.can2_tree = ttk.Treeview(self.can2_frame, selectmode = "browse",columns=colNames, displaycolumns="#all", height=25)
        self.can2_tree.heading("#0", anchor = tk.E, text = "CAN ID")
        self.can2_tree.column("#0",width=75)
        for c,w,p in zip(colNames,colWidths,colPos):
            self.can2_tree.column(c, anchor = p, stretch = False, width = w)
            self.can2_tree.heading(c, anchor = p, text = c)
        self.can2_tree.grid(row=2,column=0,columnspan=4,sticky=tk.S+tk.W)
        self.can2_frame.columnconfigure(3, weight=1)
        self.can2_frame.rowconfigure(2, weight=1)
        self.can2_unique_messages = {}
        self.can2_prior_messages = {}

        self.j1708_frame = tk.LabelFrame(self.extra_tab, text="J1708 Messages")
        self.j1708_frame.grid(row=0,column=0,sticky='NSEW',rowspan=4)


        self.stream_j1708_box =  ttk.Checkbutton(self.j1708_frame,
                                    name='stream_j1708',
                                    text="Stream J1708",
                                    command=self.send_stream_j1708)
        self.stream_j1708_box.grid(row=0,column=0,padx=5,sticky=tk.W,columnspan=2)
        self.stream_j1708_box.state(['!alternate']) #Clears Check Box

        tk.Button(self.j1708_frame,text="Clear Buffer", command=self.clear_j1708_buffer).grid(row=1,column=0,pady=5,padx=1,sticky=tk.N+tk.W)
        tk.Button(self.j1708_frame,text="Save Buffer ", command=self.save_j1708_buffer).grid(row=1,column=1,pady=5,padx=1,sticky=tk.N+tk.W)
        tk.Button(self.j1708_frame,text="Save Buffer As...", command=self.save_j1708_buffer_as).grid(row=1,column=2,pady=5,padx=1,sticky=tk.N+tk.W)
    

        self.j1708_tree = ttk.Treeview(self.j1708_frame,  height=27)
        self.j1708_tree.grid(row=3,column=0,sticky=tk.S+tk.W,columnspan=4)
        self.j1708_frame.columnconfigure(3, weight=1)
        self.j1708_frame.rowconfigure(2, weight=1)
        
        self.j1708_tree.heading("#0", anchor = 'center', text = "J1708 Messages")
        self.j1708_tree.column("#0",width=350)

        

        self.lin_frame = tk.LabelFrame(self.extra_tab, text="LIN Messages")
        self.lin_frame.grid(row=0,column=1,sticky='NSEW',rowspan=4)


        self.stream_lin_box =  ttk.Checkbutton(self.lin_frame,
                                    text="Stream LIN",
                                    command=self.send_stream_lin)
        self.stream_lin_box.grid(row=0,column=0,padx=5,sticky=tk.W,columnspan=2)
        self.stream_lin_box.state(['!alternate']) #Clears Check Box

        self.suppress_lin_box =  ttk.Checkbutton(self.lin_frame,
                                    text="Enable LIN on SSS2",
                                    command=self.send_supress_lin)
        self.suppress_lin_box.grid(row=2,column=0,padx=5,sticky=tk.W,columnspan=2)
        self.suppress_lin_box.state(['!alternate']) #Clears Check Box
        self.suppress_lin_box.state(['selected']) 

        tk.Button(self.lin_frame,text="Clear Buffer", command=self.clear_lin_buffer).grid(row=1,column=0,pady=5,padx=1,sticky=tk.N+tk.W)
        tk.Button(self.lin_frame,text="Save Buffer ", command=self.save_lin_buffer).grid(row=1,column=1,pady=5,padx=1,sticky=tk.N+tk.W)
        tk.Button(self.lin_frame,text="Save As...", command=self.save_lin_buffer_as).grid(row=1,column=2,pady=5,padx=1,sticky=tk.N+tk.W)
    

        self.lin_tree = ttk.Treeview(self.lin_frame,  height=27)
        self.lin_tree.grid(row=3,column=0,sticky=tk.S+tk.W,columnspan=4)
        self.lin_frame.columnconfigure(3, weight=1)
        self.lin_frame.rowconfigure(2, weight=1)
        
        self.lin_tree.heading("#0", anchor = 'center', text = "LIN Messages")
        self.lin_tree.column("#0",width=250)

        
    def send_stream_lin(self):
        if self.stream_lin_box.instate(['selected']):
            commandString = "LIN,1"
        else:
            commandString = "LIN,0"
        self.tx_queue.put_nowait(commandString)  

    def send_supress_lin(self):
        if self.suppress_lin_box.instate(['selected']):
            commandString = "SENDLIN,1"
        else:
            commandString = "SENDLIN,0"
        self.tx_queue.put_nowait(commandString)  
        
        
    def send_stream_A21(self):
        if self.stream_A21_box.instate(['selected']):
            commandString = "AI,1"
        else:
            commandString = "AI,0"
        self.tx_queue.put_nowait(commandString)    

    def send_stream_j1708(self):
        if self.stream_j1708_box.instate(['selected']):
            commandString = "J1708,1"
        else:
            commandString = "J1708,0"
        self.tx_queue.put_nowait(commandString)    

    def recall_command_down(self,event=None):
        self.serial_TX_message.delete(0,tk.END)
        self.serial_TX_message.insert(0,self.sent_serial_messages[self.sent_serial_messages_index])
        self.sent_serial_messages_index += 1
        if self.sent_serial_messages_index == len(self.sent_serial_messages):
            self.sent_serial_messages_index = 0
            
    def recall_command_up(self,event=None):
        self.serial_TX_message.delete(0,tk.END)
        self.serial_TX_message.insert(0,self.sent_serial_messages[self.sent_serial_messages_index])
        self.sent_serial_messages_index -= 1
        if self.sent_serial_messages_index < 0:
            self.sent_serial_messages_index = len(self.sent_serial_messages)-1
            
    def save_transcript(self):
        pass
    
    def settings_monitor_setup(self):
        
        
        self.settings_frame = tk.LabelFrame(self.monitor_tab, text="SSS2 Settings")
        self.settings_frame.grid(row=0,column=0,sticky='EW',rowspan=2)

        tk.Button(self.settings_frame,text="List SSS2 Settings",
                    command=self.send_list_settings).grid(row=0,column=0,sticky="W",padx=5,pady=5)
        #tk.Button(self.settings_frame,text="Save Transcript",
        #            command=self.save_transcript).grid(row=0,column=1,sticky="W",padx=5,pady=5)
        
        tk.Label(self.settings_frame,text="Command:").grid(row=0,column=2, sticky="E",pady=5)
        self.serial_TX_message = ttk.Entry(self.settings_frame,width=55)
        self.serial_TX_message.grid(row=0,column = 3,sticky="EW")
        self.serial_TX_message.bind('<Return>',self.send_arbitrary_serial_message)
        self.serial_TX_message.bind('<Up>',self.recall_command_up)
        self.serial_TX_message.bind('<Down>',self.recall_command_down)
        self.sent_serial_messages=[]
        self.sent_serial_messages_index=0
        
        self.settings_text = tkst.ScrolledText(self.settings_frame,wrap=tk.NONE,width=130,height=35)
        self.settings_text.grid(row=1,column=0,sticky="NSEW",columnspan=4)
   
        self.settings_frame.grid_columnconfigure(3, weight=1)

        self.analog_frame = tk.LabelFrame(self.monitor_tab, text="Analog Voltage Readings")
        self.analog_frame.grid(row=0,column=3,sticky='NSEW')
        self.analog_frame.grid_columnconfigure(3, weight=1)
        
        self.stream_A21_box =  ttk.Checkbutton(self.analog_frame,
                                    name='stream_A21',
                                    text="Stream Voltage Readings",
                                    command=self.send_stream_A21)
        self.stream_A21_box.grid(row=0,padx=5,column=0,sticky=tk.W,columnspan=3)
        self.stream_A21_box.state(['!alternate']) #Clears Check Box
        
        
        tk.Button(self.analog_frame,text="Clear Buffer", command=self.clear_analog_buffer).grid(row=1,column=0,padx=1,sticky=tk.W)
        tk.Button(self.analog_frame,text="Save Buffer ", command=self.save_analog_buffer).grid(row=1,column=1,pady=5,padx=1,sticky=tk.W)
        tk.Button(self.analog_frame,text="Save Buffer As...", command=self.save_analog_buffer_as).grid(row=1,column=2,pady=5,padx=1,sticky=tk.W)

        
        
        colWidths = [65,65,65,65,65,65]
        #colNames = ["J24:10","J24:9","J24:8","J18:13","J18:14","J24:7"]
        colNames = ["J24:10","J24:9","J24:8","J18:13"]
        colPos = ['center','center','center','center','center','center']
        self.analog_tree = ttk.Treeview(self.analog_frame, columns=colNames, height=20)
        self.analog_tree.grid(row=4,column=0,sticky=tk.W,columnspan=4)

        self.analog_tree.heading("#0", anchor = 'center', text = "Time")
        self.analog_tree.column("#0",width=65)

        for c,w,p in zip(colNames,colWidths,colPos):
            self.analog_tree.column(c, anchor = p, stretch = False, width = w)
            self.analog_tree.heading(c, anchor = p, text = c)

        self.clear_analog_buffer()

        self.calibration_frame = tk.LabelFrame(self.monitor_tab, text="Quadratic Voltage Calibrations")
        self.calibration_frame.grid(row=1,column=3,sticky='NSEW')
        col=1
        for name in colNames:
            tk.Label(self.calibration_frame,text=name).grid(row=0,column=col)
            col+=1

        tk.Label(self.calibration_frame,text="a2").grid(row=1,column=0)
        tk.Label(self.calibration_frame,text="a1").grid(row=2,column=0)
        tk.Label(self.calibration_frame,text="a0").grid(row=3,column=0)
            
        self.calibration_variable=[]
        self.calibration_entries=[]
        for i in range(len(self.settings_dict["Analog Calibration"])): #Rows
            self.calibration_variable.append([])
            self.calibration_entries.append([])
            
            for j in range(len(self.settings_dict["Analog Calibration"][i])): #Columns
                if j==4:
                    break
                self.calibration_variable[i].append(tk.StringVar(value="{}".format(self.settings_dict["Analog Calibration"][i][j])))
                self.calibration_entries[i].append(tk.Entry(self.calibration_frame, width=11,textvariable = self.calibration_variable[i][j]))
                self.calibration_entries[i][j].grid(row=i+1, column=j+1)
                self.calibration_entries[i][j].bind("<Tab>",self.adjust_calibrations)
                self.calibration_entries[i][j].bind("<Return>",self.adjust_calibrations)
              
    def adjust_calibrations(self,event=None):
        for i in range(len(self.settings_dict["Analog Calibration"])): #Rows
            for j in range(len(self.settings_dict["Analog Calibration"][i])): #Columns
                try:
                    self.settings_dict["Analog Calibration"][i][j] = float(self.calibration_variable[i][j].get())
                    self.calibration_entries[i][j]['bg']='white'
                except Exception as e:
                    print(e)
                    self.calibration_entries[i][j]['bg']='red'
                    self.root.bell()
                    
    
    def check_SSS2_connection(self):
        sss2_id = self.settings_dict["SSS2 Product Code"].strip()
        command_string = "OK,{}".format(sss2_id)
        self.tx_queue.put_nowait(command_string)
        n=0
        while (self.file_OK_received.get() == False) and n < 100 :
            time.sleep(.01)
            n+=1
        if self.file_OK_received.get() == True:
            self.file_OK_received.set(False)
            return True
        else:
            messagebox.showwarning("Valid SSS2",
                "There is not a valid unique ID from the SSS2. There might be something wrong with the USB/Serial connection.")
            return False
        
            
        
    def connect_to_serial(self):
        try:
            with open("SSS2comPort.txt","r") as comFile:
                comport = comFile.readline().strip()
            self.serial = serial.Serial(comport,baudrate=4000000,timeout=0.010,
                                    parity=serial.PARITY_ODD,write_timeout=.010,
                                    xonxoff=False, rtscts=False, dsrdtr=False)
        except:
            connection_dialog = setup_serial_connections(self)
            self.serial = connection_dialog.result
            
        print(self.serial)
        if self.serial: 
            if self.serial is not None:
                if self.serial.is_open:
                    print("SSS2 connected.")
                    self.thread = SerialThread(self,self.rx_queue,self.tx_queue,self.serial)
                    self.thread.signal = True
                    self.thread.daemon = True
                    self.thread.start()
                    print("Started Serial Thread.")
                    return
       
        messagebox.showerror("SSS2 Serial Connection Error",
                              "The SSS2 serial connection is not present. Please connect the SSS2. You may have to restart the program if the connectrion continues to fail." )                
        
    def check_serial_connection(self,event = None):
        try:
            if self.thread.signal:
                available_comports = setup_serial_connections.find_serial_ports(self)
                for port in available_comports:
                    if self.serial.port in port.split():
                        
                        self.serial_connected = self.check_SSS2_connection
                        
                        self.connection_status_string.set('SSS2 Connected on '+self.serial.port)
                        self.serial_rx_entry['bg']='white'
                        return True
        
        
            self.thread.signal = False
        except:
            pass
        self.connection_status_string.set('USB to Serial Connection Unavailable. Please install drivers and plug in the SSS2.')
        self.serial_rx_entry['bg']='red'
        if self.serial: 
            if self.serial is not None:
                self.connect_to_serial()
            else:
                self.serial.close()
        self.serial = None
        return False
    
        self.after(2000,self.check_serial_connection())
        
    def send_arbitrary_serial_message(self,event = None):
        commandString = self.serial_TX_message.get()
        self.tx_queue.put_nowait(commandString)
        self.serial_TX_message.delete(0,tk.END)
        self.sent_serial_messages.append(commandString)
        self.sent_serial_messages_index=len(self.sent_serial_messages)-1
        
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

    def send_stream_can2(self):
        if self.stream_can2_box.instate(['selected']):
            commandString = "C2,1"
        else:
            commandString = "C2,0"
        self.tx_queue.put_nowait(commandString)
            
    def send_list_settings(self):
        commandString = "LS,"
        self.tx_queue.put_nowait(commandString)
        
    def write_j1708_log_file(self,data_file_name):
        with open(data_file_name,'w') as f:
            f.write("Channel,Unix Timestamp,MID,PID,Data,Checksum,OK (Checksum Valid)\n")
            for line in self.received_j1708_messages:
                f.write(",".join(line)+"\n")
        print("Saved {}".format(data_file_name))
        self.file_status_string.set("Saved log file to "+data_file_name)

    def write_lin_log_file(self,data_file_name):
        with open(data_file_name,'w') as f:
            f.write("Timestamp,ID,B0,B1,B2,B3,Checksum,Checksum\n")
            for line in self.received_lin_messages:
                f.write(",".join(line)+"\n")
        print("Saved {}".format(data_file_name))
        self.file_status_string.set("Saved log file to "+data_file_name)

    def write_analog_log_file(self,data_file_name,message_list):
        with open(data_file_name,'w') as f:
            f.write("Analog Input Voltage Readings.\n")
            f.write("Units for time are seconds.\n")
            f.write("Units for Ports are Volts.\n")
            f.write("Voltage Readings on J24:7 require additional interior pins installed on the Teensy 3.6. See the schematics on Github for more details.\n")
            #f.write("Time,J24:10,J24:9,J24:8,J18:13,J18:14,J24:7\n")
            f.write("Time,J24:10,J24:9,J24:8,J18:13\n")
            for line in message_list:
                f.write(",".join(line)+"\n")
        print("Saved {}".format(data_file_name))
        self.file_status_string.set("Saved log file to "+data_file_name)
        
    def write_can_log_file(self,data_file_name,message_list):    
        with open(data_file_name,'w') as f:
            f.write("Channel,Unix Timestamp,CAN ID (Hex),EXT,DLC,B1,B2,B3,B4,B5,B6,B7,B8\n")
            for line in message_list:
                f.write(",".join(line)+"\n")
        print("Saved {}".format(data_file_name))
        self.file_status_string.set("Saved log file to "+data_file_name)

    def save_j1939_buffer_as(self):
        types = [('Comma Separated Values', '*.csv')]
        idir = self.home_directory
        ifile = "SSS2_J1939_Data_Log_{}.csv".format(time.strftime("%Y-%m-%d_%H%M%S", time.localtime()))
        title='Save J1939 Log File'
        data_file_name = filedialog.asksaveasfilename( filetypes=types,
                                           initialdir=idir,
                                           initialfile=ifile,
                                           title=title,
                                           defaultextension=".csv")
        self.write_can_log_file(data_file_name,received_can0_messages)
        self.clear_j1939_buffer()
        
    def save_can2_buffer_as(self):
        types = [('Comma Separated Values', '*.csv')]
        idir = self.home_directory
        ifile = "SSS2_CAN2_Data_Log_{}.csv".format(time.strftime("%Y-%m-%d_%H%M%S", time.localtime()))
        title='Save CAN2 Log File'
        data_file_name = filedialog.asksaveasfilename( filetypes=types,
                                           initialdir=idir,
                                           initialfile=ifile,
                                           title=title,
                                           defaultextension=".csv")
        
        self.write_can_log_file(data_file_name,received_can2_messages)
        self.clear_can2_buffer()

    def save_can1_buffer_as(self):
        types = [('Comma Separated Values', '*.csv')]
        idir = self.home_directory
        ifile = "SSS2_CAN1_Data_Log_{}.csv".format(time.strftime("%Y-%m-%d_%H%M%S", time.localtime()))
        title='Save CAN1 Log File'
        data_file_name = filedialog.asksaveasfilename( filetypes=types,
                                           initialdir=idir,
                                           initialfile=ifile,
                                           title=title,
                                           defaultextension=".csv")
        
        self.write_can_log_file(data_file_name,received_can1_messages)
        self.clear_can1_buffer()
        
    def save_j1708_buffer_as(self):
        types = [('Comma Separated Values', '*.csv')]
        idir = self.home_directory
        ifile = "SSS2_J1708_Data_Log_{}.csv".format(time.strftime("%Y-%m-%d_%H%M%S", time.localtime()))
        title='Save J1708 Log File'
        data_file_name = filedialog.asksaveasfilename( filetypes=types,
                                           initialdir=idir,
                                           initialfile=ifile,
                                           title=title,
                                           defaultextension=".csv")
        
        self.write_j1708_log_file(data_file_name)
        self.clear_j1708_buffer()

    def save_lin_buffer_as(self):
        types = [('Comma Separated Values', '*.csv')]
        idir = self.home_directory
        ifile = "SSS2_LIN_Data_Log_{}.csv".format(time.strftime("%Y-%m-%d_%H%M%S", time.localtime()))
        title='Save LIN Log File'
        data_file_name = filedialog.asksaveasfilename( filetypes=types,
                                           initialdir=idir,
                                           initialfile=ifile,
                                           title=title,
                                           defaultextension=".csv")
        
        self.write_lin_log_file(data_file_name)
        self.clear_lin_buffer()
        
    def save_analog_buffer_as(self):
        types = [('Comma Separated Values', '*.csv')]
        idir = self.home_directory
        ifile = "SSS2_Analog_Data_Log_{}.csv".format(time.strftime("%Y-%m-%d_%H%M%S", time.localtime()))
        title='Save Analog Voltage Log File'
        data_file_name = filedialog.asksaveasfilename( filetypes=types,
                                           initialdir=idir,
                                           initialfile=ifile,
                                           title=title,
                                           defaultextension=".csv")
        
        self.write_analog_log_file(data_file_name,self.received_analog_messages)
        self.clear_analog_buffer()
   
    def save_j1939_buffer(self):
        if os.path.exists(self.home_directory):
            data_file_name=self.home_directory + "SSS2_J1939_Data_Log_{}.csv".format(time.strftime("%Y-%m-%d_%H%M%S", time.localtime()))
        else:
            self.save_j1939_buffer_as()
        self.write_can_log_file(data_file_name,self.received_can0_messages)
        self.clear_j1939_buffer()
        
    def save_can1_buffer(self):
        if os.path.exists(self.home_directory):
            data_file_name=self.home_directory + "SSS2_CAN1_Data_Log_{}.csv".format(time.strftime("%Y-%m-%d_%H%M%S", time.localtime()))
        else:
            self.save_can1_buffer_as()
        self.write_can_log_file(data_file_name,self.received_can1_messages)
        self.clear_can1_buffer()
    def save_can2_buffer(self):
        if os.path.exists(self.home_directory):
            data_file_name=self.home_directory + "SSS2_CAN2_Data_Log_{}.csv".format(time.strftime("%Y-%m-%d_%H%M%S", time.localtime()))
        else:
            self.save_can2_buffer_as()
        self.write_can_log_file(data_file_name,self.received_can2_messages)
        self.clear_can2_buffer()
   
    def save_j1708_buffer(self):
        if os.path.exists(self.home_directory):
            data_file_name=self.home_directory + "SSS2_J1708_Data_Log_{}.csv".format(time.strftime("%Y-%m-%d_%H%M%S", time.localtime()))
        else:
            self.save_j1708_buffer_as()
        self.write_j1708_log_file(data_file_name)
        print("Saved {}".format(data_file_name))
        self.file_status_string.set("Saved log file to "+data_file_name)
        self.clear_j1708_buffer()

    def save_lin_buffer(self):
        if os.path.exists(self.home_directory):
            data_file_name=self.home_directory + "SSS2_LIN_Data_Log_{}.csv".format(time.strftime("%Y-%m-%d_%H%M%S", time.localtime()))
        else:
            self.save_lin_buffer_as()
        self.write_lin_log_file(data_file_name)
        print("Saved {}".format(data_file_name))
        self.file_status_string.set("Saved log file to "+data_file_name)
        self.clear_lin_buffer()

    def save_analog_buffer(self):
        if os.path.exists(self.home_directory):
            data_file_name=self.home_directory + "SSS2_Analog_Data_Log_{}.csv".format(time.strftime("%Y-%m-%d_%H%M%S", time.localtime()))
        else:
            self.save_analog_buffer_as()
        self.write_analog_log_file(data_file_name,self.received_analog_messages)
        print("Saved {}".format(data_file_name))
        self.file_status_string.set("Saved log file to "+data_file_name)
        self.clear_analog_buffer()
        
    def clear_j1939_buffer(self):
        self.received_can0_messages=[]
        self.j1939_prior_messages={}
        self.j1939_unique_messages={}
        for tree_item in self.j1939_tree.get_children():
            self.j1939_tree.delete(tree_item)  
        self.j1939_tree.tag_configure('dataRow',background='white')
        
    def clear_can1_buffer(self):
        self.received_can1_messages=[]
        self.can1_prior_messages={}
        self.can1_unique_messages={}
        for tree_item in self.can1_tree.get_children():
            self.can1_tree.delete(tree_item)  
        self.can1_tree.tag_configure('dataRow',background='white')
        
    def clear_can2_buffer(self):
        self.received_can2_messages=[]
        self.can2_prior_messages={}
        self.can2_unique_messages={}
        for tree_item in self.can2_tree.get_children():
            self.can2_tree.delete(tree_item)  
        self.can2_tree.tag_configure('dataRow',background='white')
    
    def clear_j1708_buffer(self):
        self.received_j1708_messages=[]
        for tree_item in self.j1708_tree.get_children():
            self.j1708_tree.delete(tree_item)  
        self.j1708_tree.tag_configure('dataRow',background='white')

    def clear_lin_buffer(self):
        self.received_lin_messages=[]
        for tree_item in self.lin_tree.get_children():
            self.lin_tree.delete(tree_item)  
        self.lin_tree.tag_configure('dataRow',background='white')

    def clear_analog_buffer(self):
        for tree_item in self.analog_tree.get_children():
            self.analog_tree.delete(tree_item) 
        self.analog_tree.tag_configure('dataRow',background='white')
        self.analog_count = 0
        
    def process_serial(self):
        try:
            limit = int(self.j1939_size_value.get())
            self.j1939_size['bg']='white'
        except:
            limit = 100000
            self.j1939_size['bg']='red'
        if self.check_serial_connection():
            while self.rx_queue.qsize():
                new_serial_line = self.rx_queue.get_nowait()
                if new_serial_line[0:4]==b'CAN0':
                    CANdata = new_serial_line.decode('ascii',"ignore").strip().split()
                         
                    if len(self.received_can0_messages) < limit:
                        try:
                            self.received_can0_messages.append(CANdata)
                            if CANdata[2] in self.j1939_prior_messages:
                                self.j1939_prior_messages[CANdata[2]]=self.j1939_unique_messages[CANdata[2]]
                                self.j1939_unique_messages[CANdata[2]]={"Timestamp":CANdata[1],"DLC":CANdata[4],"data":CANdata[5:],"count":self.j1939_prior_messages[CANdata[2]]["count"]+1}
                                period = float(self.j1939_unique_messages[CANdata[2]]["Timestamp"]) - float(self.j1939_prior_messages[CANdata[2]]["Timestamp"])
                            else:
                                self.j1939_prior_messages[CANdata[2]]={"Timestamp":CANdata[1],"DLC":CANdata[4],"data":CANdata[5:13],"count":1}
                                self.j1939_unique_messages[CANdata[2]]={"Timestamp":CANdata[1],"DLC":CANdata[4],"data":CANdata[5:13],"count":1}
                                
                                period = None
                            if self.j1939_tree.exists(CANdata[2]):
                                self.j1939_tree.set(CANdata[2],"Period","{:5f}".format(period))
                                self.j1939_tree.set(CANdata[2],"DLC",CANdata[4])
                                self.j1939_tree.set(CANdata[2],"Count",self.j1939_unique_messages[CANdata[2]]["count"])
                                for b in range(8):
                                    self.j1939_tree.set(CANdata[2],"B{}".format(b),CANdata[5+b])
                            else: 
                                self.j1939_tree.insert("",tk.END,iid=CANdata[2],text = CANdata[2],values=[None,CANdata[4]]+CANdata[5:13]+[1],tags=('dataRow',))
                            self.j1939_tree.see(CANdata[2])
                            self.j1939_tree.tag_configure('dataRow',background='white')
                        except Exception as e:
                            print(e)
                            self.j1939_tree.tag_configure('dataRow',background='orange')
                    else:
                        self.j1939_tree.tag_configure('dataRow',background='orange')
                            
                elif new_serial_line[0:4]==b'CAN1':
                    CANdata = new_serial_line.decode('ascii',"ignore").strip().split()
                    if len(self.received_can1_messages) < limit:
                        try:
                            self.received_can1_messages.append(CANdata)
                            if CANdata[2] in self.can1_prior_messages:
                                self.can1_prior_messages[CANdata[2]]=self.can1_unique_messages[CANdata[2]]
                                self.can1_unique_messages[CANdata[2]]={"Timestamp":CANdata[1],"DLC":CANdata[4],"data":CANdata[5:],"count":self.can1_prior_messages[CANdata[2]]["count"]+1}
                                period = float(self.can1_unique_messages[CANdata[2]]["Timestamp"]) - float(self.can1_prior_messages[CANdata[2]]["Timestamp"])
                            else:
                                self.can1_prior_messages[CANdata[2]]={"Timestamp":CANdata[1],"DLC":CANdata[4],"data":CANdata[5:13],"count":1}
                                self.can1_unique_messages[CANdata[2]]={"Timestamp":CANdata[1],"DLC":CANdata[4],"data":CANdata[5:13],"count":1}
                                
                                period = None
                            if self.can1_tree.exists(CANdata[2]):
                                self.can1_tree.set(CANdata[2],"Period","{:5f}".format(period))
                                self.can1_tree.set(CANdata[2],"DLC",CANdata[4])
                                self.can1_tree.set(CANdata[2],"Count",self.can1_unique_messages[CANdata[2]]["count"])
                                for b in range(8):
                                    self.can1_tree.set(CANdata[2],"B{}".format(b),CANdata[5+b])
                            else: 
                                self.can1_tree.insert("",tk.END,iid=CANdata[2],text = CANdata[2],values=[None,CANdata[4]]+CANdata[5:13]+[1],tags=('dataRow',))
                            self.can1_tree.see(CANdata[2])
                            self.can1_tree.tag_configure('dataRow',background='white')
                        except Exception as e:
                            print(e)
                            self.can1_tree.tag_configure('dataRow',background='orange')
                    else:
                        self.can1_tree.tag_configure('dataRow',background='orange')
                     
                elif new_serial_line[0:4]==b'CAN2':
                    CANdata = new_serial_line.decode('ascii',"ignore").strip().split()
                    if len(self.received_can2_messages) < limit:
                        try:
                            self.received_can2_messages.append(CANdata)
                            if CANdata[2] in self.can2_prior_messages:
                                self.can2_prior_messages[CANdata[2]]=self.can2_unique_messages[CANdata[2]]
                                self.can2_unique_messages[CANdata[2]]={"Timestamp":CANdata[1],"DLC":CANdata[4],"data":CANdata[5:],"count":self.can2_prior_messages[CANdata[2]]["count"]+1}
                                period = float(self.can2_unique_messages[CANdata[2]]["Timestamp"]) - float(self.can2_prior_messages[CANdata[2]]["Timestamp"])
                            else:
                                self.can2_prior_messages[CANdata[2]]={"Timestamp":CANdata[1],"DLC":CANdata[4],"data":CANdata[5:13],"count":1}
                                self.can2_unique_messages[CANdata[2]]={"Timestamp":CANdata[1],"DLC":CANdata[4],"data":CANdata[5:13],"count":1}
                                
                                period = None
                            if self.can2_tree.exists(CANdata[2]):
                                self.can2_tree.set(CANdata[2],"Period","{:5f}".format(period))
                                self.can2_tree.set(CANdata[2],"DLC",CANdata[4])
                                self.can2_tree.set(CANdata[2],"Count",self.can2_unique_messages[CANdata[2]]["count"])
                                for b in range(8):
                                    self.can2_tree.set(CANdata[2],"B{}".format(b),CANdata[5+b])
                            else: 
                                self.can2_tree.insert("",tk.END,iid=CANdata[2],text = CANdata[2],values=[None,CANdata[4]]+CANdata[5:13]+[1],tags=('dataRow',))
                            self.can2_tree.see(CANdata[2])
                            self.can2_tree.tag_configure('dataRow',background='white')
                        except Exception as e:
                            print(e)
                            self.can2_tree.tag_configure('dataRow',background='orange')
                    else:
                        self.can2_tree.tag_configure('dataRow',background='orange')
                     
                elif new_serial_line[0:3]==b'LIN':
                    LINdata = new_serial_line.decode('ascii',"ignore").strip().split(',')
                    self.received_lin_messages.append(LINdata)
                    latest = self.lin_tree.insert("",tk.END,text = LINdata[1:])
                    self.lin_tree.see(latest)
                elif new_serial_line[0:5]==b'J1708':
                    J1708Data = new_serial_line.decode('ascii',"ignore").strip().split()
                    self.received_j1708_messages.append(J1708Data)
                    latest = self.j1708_tree.insert("",tk.END,text = J1708Data[2:-1])
                    self.j1708_tree.see(latest)

                elif new_serial_line[0:6]==b'ANALOG':
                    self.analog_count += 1
                    if self.analog_count < limit:
                        analog_data = new_serial_line[7:].decode('ascii',"ignore").strip().split()
                        #print(analog_data)
                        analog_time="{:>0.3f}".format(float(analog_data[0])/1000)
                        analog_list = []
                        for i in range(len(self.settings_dict["Analog Calibration"][0])):
                            if i==4:
                                break
                            analog_data.append(0) #makes sure data streams have values
                            analog_list.append("{:>0.3f}".format(self.settings_dict["Analog Calibration"][0][i]*float(analog_data[i+1])*float(analog_data[i+1])
                                                           + self.settings_dict["Analog Calibration"][1][i]*float(analog_data[i+1])
                                                           + self.settings_dict["Analog Calibration"][2][i]))
                        latest = self.analog_tree.insert("",tk.END,text = analog_time ,values=analog_list,tags=('dataRow',))
                        self.analog_tree.see(latest)
                        self.analog_tree.tag_configure('dataRow',background='white')
                        self.received_analog_messages.append([analog_time]+analog_list[:len(self.settings_dict["Analog Calibration"][0])])
                    else:
                        self.analog_tree.tag_configure('dataRow',background='orange')
                   
                elif new_serial_line[:16]==b'OK:Authenticated':
                    self.file_authenticated = True
                    self.file_OK_received.set(True)
                elif new_serial_line[0:9]==b'OK:Denied':
                    self.file_authenticated = False
                    self.file_OK_received.set(True)
                elif new_serial_line[0:23]==b'INFO SSS2 Component ID:':
                    temp_data = str(new_serial_line,'utf-8').split(':')
                    self.sss_component_id_text.set(temp_data[1].strip())
                elif new_serial_line[0:8]==b'FIRMWARE':
                    temp_data = str(new_serial_line,'utf-8').split()
                    self.sss_software_id_text.set(temp_data[1].strip())
                elif new_serial_line[0:4]==b'ID: ':
                    temp_data = str(new_serial_line[4:],'utf-8').strip()
                    if self.sss2_product_code_text.get().strip() is not "UNIVERSAL":
                        self.sss2_product_code_text.set(temp_data)
                    self.unique_ID = temp_data
                    self.sss2_product_code['bg']='white'
                elif new_serial_line[0:8]==b'SET 50,1':
                    self.ignition_key_button.state(['selected'])
                elif new_serial_line[0:8]==b'SET 50,0':
                    self.ignition_key_button.state(['!selected'])
                else:
                    self.file_OK_received.set(True)
                if new_serial_line[0:4]!=b'CAN0' and new_serial_line[0:4]!=b'CAN1' and new_serial_line[0:4]!=b'CAN2' and new_serial_line[0:5]!=b'J1708' and new_serial_line[0:6]!=b'ANALOG' and new_serial_line[0:4]!=b'LIN ':
                    self.serial_rx_entry.delete(0,tk.END)
                    self.serial_rx_entry.insert(0, new_serial_line.decode('ascii',"ignore"))
                    self.settings_text.insert(tk.END,new_serial_line.decode('ascii',"ignore"))
                    self.settings_text.see(tk.END)
                
        self.after(50, self.process_serial)
    
    def potentiometer_settings(self):
        """Adjusts the potentiometers and other analog outputs"""

        self.pot_bank={}
        row_index=0
        pot_dict=self.settings_dict["Potentiometers"]
        for bank_key in sorted(pot_dict.keys()):
            if bank_key == "Others":
                self.pot_bank[bank_key] = pot_bank(self.extra_tab,self.tx_queue,pot_dict,bank_key,row=0,col=2,colspan=1)
            else:
                self.pot_bank[bank_key] = pot_bank(self.settings_tab,self.tx_queue,pot_dict,bank_key,row=row_index,col=0,colspan=4)
            row_index += 1
 
        self.settings_tab.grid_columnconfigure(0,weight=1)
        self.settings_tab.grid_columnconfigure(1,weight=1)
        self.settings_tab.grid_columnconfigure(2,weight=1)
        self.settings_tab.grid_columnconfigure(3,weight=1)
               
        self.twelve2_switch = config_switches(self.settings_tab,self.tx_queue,
                            self.settings_dict["Switches"],"12V Out 2",row=2,col=1)
        self.ground2_switch = config_switches(self.settings_tab,self.tx_queue,
                            self.settings_dict["Switches"],"Ground Out 2",row=3,col=1)

                

    def send_ignition_key_command(self,event=None):
        commandString = "50,0"    
        if self.ignition_key_button.instate(['selected']):
            self.root.bell()
            if messagebox.askyesno("Turn Key Switch On","Have you loaded or configured the desired settings?\n Would you like to turn on the key switch?"):
                commandString = "50,1"
        self.tx_queue.put_nowait(commandString)
     
    def on_quit(self,event=None):
        """Exits program."""
        
        destroyer()
      

    
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
        if self.pot_dict[self.bank_key]["Terminal A Connection"] is not None:
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
                                              orient = tk.VERTICAL, length = 100,
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
        self.set_wiper_voltage()

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
    def __init__(self, parent,tx_queue,sss2_settings, row = 2, col = 0, software_ID = ""):
        self.root = parent
        self.tx_queue = tx_queue
        self.sss_software_id_text = software_ID
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

        self.set_dac_voltage()
        
        self.ecu_app = ecu_application(self.dac_frame,self.settings_dict,row=1,column=0,columnspan=3)
   
   
    def set_dac_voltage(self,event=None):
            
        self.dac_mean_position_value.delete(0,tk.END)
        self.dac_mean_position_value.insert(0,self.dac_mean_slider.get()/100)
        x=float(self.dac_mean_position_value.get())
        if self.setting_num == 49:
            if 'REV05' in self.sss_software_id_text.get():
                dac_raw_setting = int(19.985*x - 37.522) ##Special for Rev5
            else:
                dac_raw_setting = int(4.2646*x - 16.788) ##Special for Rev3
            if dac_raw_setting < 0:
               dac_raw_setting = 0 
        else:
            slope = 4095/(self.high-self.low)
            dac_raw_setting = int(slope*(x - self.low))
        commandString = "{},{:d}".format(self.setting_num,dac_raw_setting)
        self.tx_queue.put_nowait(commandString)
        
    
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
        self.freq_setting_num = self.settings_dict["SSS2 freq setting"]
        self.setup_pwm_widget()
        
    def setup_pwm_widget(self):
         
        self.pwm_frame = tk.LabelFrame(self.root, name=self.name,text=self.label)
        self.pwm_frame.grid(row=self.row,column=self.col,sticky=tk.W,padx=5,pady=5)
        
        self.pwm_duty_cycle_slider = tk.Scale(self.pwm_frame,
                                        from_ = 0,
                                        to = 100,
                                        digits = 1, resolution = 0.1,
                                        orient = tk.HORIZONTAL, length = 90,
                                        sliderlength = 10, showvalue = 0, 
                                        label = "Duty Cycle (%)",
                                        name = self.name+'_duty_cycle',
                                        command = self.set_pwm_duty_cycle)
        self.pwm_duty_cycle_slider.grid(row=0,column=0)
        self.pwm_duty_cycle_value = ttk.Entry(self.pwm_frame,width=5)
        self.pwm_duty_cycle_value.grid(row=0,column = 1,sticky="SE")
        self.pwm_duty_cycle_slider.set(self.settings_dict["Duty Cycle"])
        self.pwm_duty_cycle_value.insert(0,self.pwm_duty_cycle_slider.get())
        self.pwm_duty_cycle_value.bind('<Return>',self.set_pwm_duty_cycle_slider)
        self.pwm_duty_cycle_value.icursor(tk.END)
        self.pwm_duty_cycle_value.focus_set()
        self.set_pwm_duty_cycle_slider()
        
        self.wiper_position_button = ttk.Button(self.pwm_frame,text="Set Duty Cycle",
                                                width=14,
                                            command = self.set_pwm_duty_cycle_slider)
        self.wiper_position_button.grid(row=0,column = 2,sticky="SW",columnspan=1)


        self.pwm_frequency_slider = tk.Scale(self.pwm_frame,
                                        from_ = self.settings_dict["Lowest Frequency"],
                                        to = self.settings_dict["Highest Frequency"],
                                        digits = 1,
                                        resolution = 0.1,#(self.settings_dict["Highest Frequency"] -
                                                      #self.settings_dict["Lowest Frequency"])/200,
                                        orient = tk.HORIZONTAL, length = 90,
                                        sliderlength = 14, showvalue = 0, 
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

        self.set_pwm_frequency()
        self.set_pwm_duty_cycle()

        self.ecu_app = ecu_application(self.pwm_frame,self.settings_dict,row=2,column=0,columnspan=3)
   
    def set_pwm_frequency(self,event=None):
        self.pwm_frequency_value.delete(0,tk.END)
        self.pwm_frequency_value.insert(0,self.pwm_frequency_slider.get())
        
        slope = 1
        pwm_raw_setting = int(slope*(float(self.pwm_frequency_value.get())))
        commandString = "{},{}".format(self.freq_setting_num,pwm_raw_setting)
        self.tx_queue.put_nowait(commandString)
        

    def set_pwm_duty_cycle(self,event=None):
             
        self.pwm_duty_cycle_value.delete(0,tk.END)
        self.pwm_duty_cycle_value.insert(0,self.pwm_duty_cycle_slider.get())
        
        slope = 4096/100
        pwm_raw_setting = int(slope*(float(self.pwm_duty_cycle_value.get())))
        commandString = "{},{}".format(self.setting_num,pwm_raw_setting)
        self.tx_queue.put_nowait(commandString)
        

    def set_pwm_frequency_slider(self,event=None):
        entry_value = self.pwm_frequency_value.get()
        self.pwm_frequency_value['foreground'] = "black"
        try:
            self.pwm_frequency_slider.set(float(entry_value))
            self.set_pwm_frequency()
        except Exception as e:
            print(e)
            self.root.bell()
            self.pwm_frequency_value['foreground'] = "red"
    
    def set_pwm_duty_cycle_slider(self,event=None):
        entry_value = self.pwm_duty_cycle_value.get()
        self.pwm_duty_cycle_value['foreground'] = "black"
        try:
            self.pwm_duty_cycle_slider.set(float(entry_value))
            self.set_pwm_duty_cycle()
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

        colors=[" ","PPL/WHT","BRN/WHT","YEL/BLK","PNK/BLK","BLUE","GRN/BLK","ORN/BLK","YEL/RED","RED/WHT",
                "RED/BLK","BLU/WHT","TAN/BLK","BROWN","BLK/WHT","GRN/WHT","TAN/RED","PURPLE","PINK","TAN",
                "ORANGE","GREEN","YELLOW","RED","BLACK","RED/GRN","YEL/GRN"]

        
        self.ecu_frame = tk.LabelFrame(self.root,name='ecu_frame',text="ECU Application")
        self.ecu_frame.grid(row=self.row,column=self.col,columnspan=self.colspan,
                            rowspan=self.rowspan,sticky=tk.E+tk.W)
        self.ecu_frame.grid_columnconfigure(1,weight=2)
        self.ecu_frame.grid_columnconfigure(3,weight=2)
        
        tk.Label(self.ecu_frame,text="Pin").grid(row=0,column=0, sticky=tk.W)
        self.ecu_pins = ttk.Entry(self.ecu_frame,width=9,name="ecu pins")
        self.ecu_pins.insert(0,self.settings_dict["ECU Pins"])
        self.ecu_pins.grid(row=0,column=1,sticky=tk.W)

        #tk.Label(self.ecu_frame,text="Wire").grid(row=0,column=2, sticky=tk.W)
        self.ecu_color = ttk.Combobox(self.ecu_frame,name="color",values=sorted(colors),width=9)
        self.ecu_color.insert(0,self.settings_dict["Wire Color"])
        self.ecu_color.grid(row=0,column=3,sticky=tk.E)
        
        self.ecu_app = tk.Entry(self.ecu_frame,name="ecu application")
        self.ecu_app.insert(tk.END,self.settings_dict["Application"])
        self.ecu_app.grid(row=1,column=0,columnspan=4,sticky=tk.E+tk.W)

def destroyer():
    try:
        mainwindow.tx_queue.put_nowait("50,0")
        time.sleep(.3)
        mainwindow.serial.close()
    except Exception as e:
        print(e)
    root.quit()
    root.destroy()
    sys.exit()

        
if __name__ == '__main__':

    root = tk.Tk()
    mainwindow = SSS2(root,name='sss2')
    root.protocol("WM_DELETE_WINDOW",destroyer)
    root.mainloop()
    destroyer()
    
