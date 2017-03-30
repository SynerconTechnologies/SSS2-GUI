#SSS2 Default Settings Generator
import json

def get_default_settings():

    settings = {}
    settings["Component ID"] = "SYNER*SSS2-R03*XXXX*UNIVERSAL"
    settings["Software ID"]="SSS2*0.4*"
    
    settings["Potentiometers"]={}
    p=settings["Potentiometers"]
    p["Group A"]={}
    p["Group B"]={}
    p["Others"]={}

    g=p["Group A"]
    g["Terminal A Connection"]=True
    g["SSS2 Setting"] = 73
    g["Pairs"]={"U1U2":{},"U3U4":{},"U5U6":{},"U7U8":{}}
    
    pair = g["Pairs"]["U1U2"]
    pair["Terminal A Voltage"] = "+5V"
    pair["SSS Setting"] = 25
    pair["Name"]="U1 and U2"
    pair["Pots"] = {"U1":{},"U2":{}}

    u=pair["Pots"]["U1"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=210
    u["Pin"]="J24:1"
    u["Port"]="1"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Potentiometer 1"
    u["SSS2 Wiper Setting"]=1
    u["SSS2 TCON Setting"]=51
    u["Resistance"]="10k"
    
    u=pair["Pots"]["U2"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=200
    u["Pin"]="J24:2"
    u["Port"]="2"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Potentiometer 2"
    u["SSS2 Wiper Setting"]=2
    u["SSS2 TCON Setting"]=52
    u["Resistance"]="10k"

    pair = g["Pairs"]["U3U4"]
    pair["Terminal A Voltage"] = "+12V"
    pair["SSS Setting"] = 26
    pair["Name"]="U3 and U4"
    pair["Pots"] = {"U3":{},"U4":{}}

    u=pair["Pots"]["U3"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=190
    u["Pin"]="J24:3"
    u["Port"]="3"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Potentiometer 3"
    u["SSS2 Wiper Setting"]=3
    u["SSS2 TCON Setting"]=53
    u["Resistance"]="10k"
    
    u=pair["Pots"]["U4"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=False
    u["Wiper Connect"]=True
    u["Wiper Position"]=180
    u["Pin"]="J24:4"
    u["Port"]="4"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Potentiometer 4"
    u["SSS2 Wiper Setting"]=4
    u["SSS2 TCON Setting"]=54
    u["Resistance"]="10k"
        
    pair = g["Pairs"]["U5U6"]
    pair["Terminal A Voltage"] = "+12V"
    pair["SSS Setting"] = 27
    pair["Name"]="U5 and U6"
    pair["Pots"] = {"U5":{},"U6":{}}

    u=pair["Pots"]["U5"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=170
    u["Pin"]="J24:5"
    u["Port"]="5"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Potentiometer 5"
    u["SSS2 Wiper Setting"]=5
    u["SSS2 TCON Setting"]=55
    u["Resistance"]="10k"
    
    u=pair["Pots"]["U6"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=160
    u["Pin"]="J24:6"
    u["Port"]="6"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Potentiometer 6"
    u["SSS2 Wiper Setting"]=6
    u["SSS2 TCON Setting"]=56
    u["Resistance"]="100k"
    
    pair = g["Pairs"]["U7U8"]
    pair["Terminal A Voltage"] = "+12V"
    pair["SSS Setting"] = 28
    pair["Name"]="U7 and U8"
    pair["Pots"] = {"U7":{},"U8":{}}

    u=pair["Pots"]["U7"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=150
    u["Pin"]="J24:7"
    u["Port"]="7"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Potentiometer 7"
    u["SSS2 Wiper Setting"]=7
    u["SSS2 TCON Setting"]=57
    u["Resistance"]="100k"
    
    u=pair["Pots"]["U8"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=140
    u["Pin"]="J24:8"
    u["Port"]="8"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Potentiometer 8"
    u["SSS2 Wiper Setting"]=8
    u["SSS2 TCON Setting"]=58
    u["Resistance"]="100k"
    


    g=p["Group B"]
    g["Terminal A Connection"]=True
    g["SSS2 Setting"] = 74
    g["Pairs"]={"U9U10":{},"U11U12":{},"U13U14":{},"U15U16":{}}
    
    pair = g["Pairs"]["U9U10"]
    pair["SSS Setting"] = 29
    pair["Terminal A Voltage"] = "+12V"
    pair["Name"]="U9 and U10"
    pair["Pots"] = {"U9":{},"U10":{}}

    u=pair["Pots"]["U9"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=130
    u["Pin"]= "J24:9"
    u["Port"]= "9"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Potentiometer 9"
    u["SSS2 Wiper Setting"]=9
    u["SSS2 TCON Setting"]=59
    u["Resistance"]="10k"
    
    u=pair["Pots"]["U10"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=120
    u["Pin"]= "J24:10"
    u["Port"]="10"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Potentiometer 10"
    u["SSS2 Wiper Setting"]=10
    u["SSS2 TCON Setting"]=60
    u["Resistance"]="100k"

    pair = g["Pairs"]["U11U12"]
    pair["Terminal A Voltage"] = "+12V"
    pair["SSS Setting"] = 30
    pair["Name"]="U11 and U12"
    pair["Pots"] = {"U11":{},"U12":{}}

    u=pair["Pots"]["U11"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=110
    u["Pin"]="J24:11"
    u["Port"]="11"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Potentiometer 11"
    u["SSS2 Wiper Setting"]=11
    u["SSS2 TCON Setting"]=61
    u["Resistance"]="10k"
    
    u=pair["Pots"]["U12"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=100
    u["Pin"]="J24:12"
    u["Port"]="12"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Potentiometer 12"
    u["SSS2 Wiper Setting"]=12
    u["SSS2 TCON Setting"]=62
    u["Resistance"]="100k"
        
    pair = g["Pairs"]["U13U14"]
    pair["Terminal A Voltage"] = "+12V"
    pair["SSS Setting"] = 31
    pair["Name"]="U13 and U14"
    pair["Pots"] = {"U13":{},"U14":{}}

    u=pair["Pots"]["U13"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=90
    u["Pin"]="J24:13"
    u["Port"]="13"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Potentiometer 13"
    u["SSS2 Wiper Setting"]=13
    u["SSS2 TCON Setting"]=63
    u["Resistance"]="10k"
    
    u=pair["Pots"]["U14"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=80
    u["Pin"]="J24:14"
    u["Port"]="14"
    u["ECU Pins"] = "ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Potentiometer 14"
    u["SSS2 Wiper Setting"]=14
    u["SSS2 TCON Setting"]=64
    u["Resistance"]="100k"
    
    pair = g["Pairs"]["U15U16"]
    pair["Terminal A Voltage"] = "+12V"
    pair["SSS Setting"] = 32
    pair["Name"]="U5 and U6"
    pair["Pots"] = {"U15":{},"U16":{}}

    u=pair["Pots"]["U15"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=70
    u["Pin"]= "J24:15"
    u["Port"]="15"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Potentiometer 15"
    u["SSS2 Wiper Setting"]=15
    u["SSS2 TCON Setting"]=65
    u["Resistance"]="10k"
    
    u=pair["Pots"]["U16"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=60
    u["Pin"]= "J24:16"
    u["Port"]= "16"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Potentiometer 16"
    u["SSS2 Wiper Setting"]=16
    u["SSS2 TCON Setting"]=66
    u["Resistance"]="100k"
    


    g=p["Others"]
    g["Terminal A Connection"]=None
    g["Pairs"]={"I2CPots":{}}
    
    pair = g["Pairs"]["I2CPots"]
    pair["Terminal A Voltage"] = "+5V Fixed"
    pair["Pots"] = {"U34":{},"U36":{},"U37":{}}

    u=pair["Pots"]["U34"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=20
    u["Pin"]= "J18:12"
    u["Port"]= "28"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Port 28 Potentiometer"
    u["SSS2 Wiper Setting"]=75
    u["SSS2 TCON Setting"]=78
    u["Resistance"]="100k"
    
    u=pair["Pots"]["U36"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=50
    u["Pin"]= "J18:132"
    u["Port"]= "29"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Port 29 Potentiometer"
    u["SSS2 Wiper Setting"]=76
    u["SSS2 TCON Setting"]=79
    u["Resistance"]="10k"

    u=pair["Pots"]["U37"]
    u["Term. A Connect"]=True
    u["Term. B Connect"]=True
    u["Wiper Connect"]=True
    u["Wiper Position"]=50
    u["Pin"]= "J18:14"
    u["Port"]= "30"
    u["ECU Pins"]="ECU Pins"
    u["Application"]="Application Description"
    u["Name"]="Port 30 Potentiometer"
    u["SSS2 Wiper Setting"]=77
    u["SSS2 TCON Setting"]=80
    u["Resistance"]="100k"
    
    settings["DACs"]={}
    for i in range(1,9):
        settings["DACs"]["Vout{}".format(i)]={}

    d=settings["DACs"]["Vout1"]
    d["Lowest Voltage"]=0
    d["Highest Voltage"]=5
    d["Average Voltage"]=2.5 #DC value
    d["Amplitude"]=0
    d["SSS2 setting"] = 17
    d["Show Amplitude"]=False
    d["Frequency"]=0
    d["Show Frequency"]=False
    d["Shape"]="Constant" #Sine, Square, Triangle or Sawtooth
    d["ECU Pins"]="ECU Pins"
    d["Application"]="Application Description"
    d["Pin"]= "J18:2"
    d["Port"]= "18"
    d["Alt. Pin"]="J24:15"
    d["Alt. Pin Connect"]=False
    d["Name"] = "Vout 2-A"
     
    d=settings["DACs"]["Vout2"]
    d["Lowest Voltage"]=0
    d["Highest Voltage"]=5
    d["Average Voltage"]=2.5 #DC value
    d["SSS2 setting"] = 18
    d["Amplitude"]=0
    d["Show Amplitude"]=False
    d["Frequency"]=0
    d["Show Frequency"]=False
    d["Shape"]="Constant" #Sine, Square, Triangle or Sawtooth
    d["ECU Pins"]="ECU Pins"
    d["Application"]="Application Description"
    d["Pin"]= "J18:3"
    d["Port"]= "19"
    d["Alt. Pin"]="J24:10"
    d["Alt. Pin Connect"]=False
    d["Name"] = "Vout 2-B"
 

    d=settings["DACs"]["Vout3"]
    d["Lowest Voltage"]=0
    d["Highest Voltage"]=5
    d["Average Voltage"]=2.5 #DC value
    d["Amplitude"]=0
    d["SSS2 setting"] = 19
    d["Show Amplitude"]=False
    d["Frequency"]=0
    d["Show Frequency"]=False
    d["Shape"]="Constant" #Sine, Square, Triangle or Sawtooth
    d["ECU Pins"]="ECU Pins"
    d["Application"]="Application Description"
    d["Pin"]= "J18:4"
    d["Port"]= "20"
    d["Alt. Pin"]=None
    d["Alt. Pin Connect"]=False
    d["Name"] = "Vout 2-C"
  
    d=settings["DACs"]["Vout4"]
    d["Lowest Voltage"]=0
    d["Highest Voltage"]=5
    d["Average Voltage"]=2.5 #DC value
    d["SSS2 setting"] = 20
    d["Amplitude"]=0
    d["Show Amplitude"]=False
    d["Frequency"]=0
    d["Show Frequency"]=False
    d["Shape"]="Constant" #Sine, Square, Triangle or Sawtooth
    d["ECU Pins"]="ECU Pins"
    d["Application"]="Application Description"
    d["Pin"]= "J18:5"
    d["Port"]= "21"
    d["Alt. Pin"]=None
    d["Alt. Pin Connect"]=False
    d["Name"] = "Vout 2-D"
 
    d=settings["DACs"]["Vout5"]
    d["Lowest Voltage"]=0
    d["Highest Voltage"]=5
    d["Average Voltage"]=2.5 #DC value
    d["SSS2 setting"] = 21
    d["Amplitude"]=0
    d["Show Amplitude"]=False
    d["Frequency"]=0
    d["Show Frequency"]=False
    d["Shape"]="Constant" #Sine, Square, Triangle or Sawtooth
    d["ECU Pins"]="ECU Pins"
    d["Application"]="Application Description"
    d["Pin"]= "J18:6"
    d["Port"]= "22"
    d["Alt. Pin"]=None
    d["Alt. Pin Connect"]=False
    d["Name"] = "Vout 2-E"
 
    d=settings["DACs"]["Vout6"]
    d["Lowest Voltage"]=0
    d["Highest Voltage"]=5
    d["Average Voltage"]=2.5 #DC value
    d["SSS2 setting"] = 22
    d["Amplitude"]=0
    d["Show Amplitude"]=False
    d["Frequency"]=0
    d["Show Frequency"]=False
    d["Shape"]="Constant" #Sine, Square, Triangle or Sawtooth
    d["ECU Pins"]="ECU Pins"
    d["Application"]="Application Description"
    d["Pin"]= "J18:7"
    d["Port"]= "23"
    d["Alt. Pin"]=None
    d["Alt. Pin Connect"]=False
    d["Name"] = "Vout 2-F"

    d=settings["DACs"]["Vout7"]
    d["Lowest Voltage"]=0
    d["Highest Voltage"]=5
    d["Average Voltage"]=2.5 #DC value
    d["SSS2 setting"] = 23
    d["Amplitude"]=0
    d["Show Amplitude"]=False
    d["Frequency"]=0
    d["Show Frequency"]=False
    d["Shape"]="Constant" #Sine, Square, Triangle or Sawtooth
    d["ECU Pins"]="ECU Pins"
    d["Application"]="Application Description"
    d["Pin"]= "J18:8"
    d["Port"]= "24"
    d["Alt. Pin"]=None
    d["Alt. Pin Connect"]=False
    d["Name"] = "Vout 2-G"

    d=settings["DACs"]["Vout8"]
    d["Lowest Voltage"]=0
    d["Highest Voltage"]=5
    d["Average Voltage"]=2.5 #DC value
    d["SSS2 setting"] = 24
    d["Amplitude"]=0
    d["Show Amplitude"]=False
    d["Frequency"]=0
    d["Show Frequency"]=False
    d["Shape"]="Constant" #Sine, Square, Triangle or Sawtooth
    d["ECU Pins"]="ECU Pins"
    d["Application"]="Application Description"
    d["Pin"]= "J18:9"
    d["Port"]= "25"
    d["Alt. Pin"]=None
    d["Alt. Pin Connect"]=False
    d["Name"] = "Vout 2-H"
 
    settings["PWMs"]={}
    for i in range(1,5):
        settings["PWMs"]["PWM{}".format(i)]={}

    d=settings["PWMs"]["PWM1"]
    d["Name"] = "PWM1"
    d["Lowest Voltage"]=0
    d["Highest Voltage"]=5
    d["Duty Cycle"]=127 
    d["SSS2 setting"] = 33
    d["Frequency"]=200
    d["SSS2 freq setting"] = 81
    d["Show Frequency"]=True
    d["ECU Pins"]="ECU Pins"
    d["Application"]="Application Description"
    d["Port"]= "31"
    d["Pin"]= "J18:15"
    d["Pin Connect"]=True
    d["SSS2 pin setting"] = 67
    d["Alt. Port"]="13"
    d["Alt. Pin"]="J24:13"
    d["Alt. Pin Connect"]=True
    d["SSS2 alt setting"] = 40


    d=settings["PWMs"]["PWM2"]
    d["Name"] = "PWM2"
    d["Lowest Voltage"]=0
    d["Highest Voltage"]=5
    d["Duty Cycle"]=127 
    d["SSS2 setting"] = 34
    d["Frequency"]=200
    d["SSS2 freq setting"] = 82
    d["Show Frequency"]=True
    d["ECU Pins"]="ECU Pins"
    d["Application"]="Application Description"
    d["Port"]= "32"
    d["Pin"]= "J18:16"
    d["Pin Connect"]=True
    d["SSS2 pin setting"] = 68
    d["Alt. Port"]="14"
    d["Alt. Pin"]="J24:14"
    d["Alt. Pin Connect"]=True
    d["SSS2 alt setting"] = 40

    d=settings["PWMs"]["PWM3"]
    d["Name"] = "PWM3"
    d["Lowest Voltage"]=0
    d["Highest Voltage"]=5
    d["Duty Cycle"]=127 
    d["SSS2 setting"] = 35
    d["Frequency"]=200
    d["SSS2 freq setting"] = 83
    d["Show Frequency"]=True
    d["ECU Pins"]="ECU Pins"
    d["Application"]="Application Description"
    d["Port"]= "27"
    d["Pin"]= "J18:10"
    d["Pin Connect"]=True
    d["SSS2 pin setting"] = 69
    d["Alt. Port"]=None
    d["Alt. Pin"]=None
    d["Alt. Pin Connect"]=None
    d["SSS2 alt setting"] =None

    d=settings["PWMs"]["PWM4"]
    d["Name"] = "PWM4"
    d["Lowest Voltage"]=0
    d["Highest Voltage"]=5
    d["Duty Cycle"]=127 
    d["SSS2 setting"] = 36
    d["Frequency"]=200
    d["SSS2 freq setting"] = 84
    d["Show Frequency"]=True
    d["ECU Pins"]="ECU Pins"
    d["Application"]="Application Description"
    d["Port"]= "17"
    d["Pin"]= "J18:1"
    d["Pin Connect"]=True
    d["SSS2 pin setting"] = 70
    d["Alt. Port"]=None
    d["Alt. Pin"]=None
    d["Alt. Pin Connect"]=None
    d["SSS2 alt setting"] =None

    settings["HVAdjOut"]={}
    d=settings["HVAdjOut"]
    d["Lowest Voltage"]=4
    d["Highest Voltage"]=12
    d["Average Voltage"]=8 #DC value
    d["SSS2 setting"] = 49
    d["ECU Pins"]="ECU Pins"
    d["Application"]="Application Description"
    d["Pin"]= "J24:19"
    d["Alt. Pin"]="J18:11"
    d["Name"] = "High Current Regulator"
    
    settings["Switches"]={}
    s=settings["Switches"]
    s["11 Port 10 or 19"]={"SSS2 setting":37,"State":False,"Label":"Connect Vout 2 to Port 10 (J24:10)"}
    s["12 Port 15 or 18"]={"SSS2 setting":38,"State":False,"Label":"Connect Vout 1 to Port 15 (J24:15)"}
    s["13 CAN1 or J1708"]={"SSS2 setting":39,"State":True,"Label":"Connect J1708 to J24:17 and J24:17"}
    s["14 PWMs or CAN2"]={"SSS2 setting":40,"State":True,"Label":"Connect CAN2 to J18:15 and J18:16"}
    s["01 CAN0 Termination Resistor"]={"SSS2 setting":41,"State":True,"Label":"Connect CAN0 Termination Resistor"}
    s["02 CAN1 Termination Resistor"]={"SSS2 setting":42,"State":True,"Label":"Connect CAN1 Termination Resistor"}
    s["03 CAN2 Termination Resistor"]={"SSS2 setting":43,"State":True,"Label":"Connect CAN2 Termination Resistor"}
    s["04 LIN Master Pullup Resistor"]={"SSS2 setting":44,"State":True,"Label":"Connect LIN Master Pullup Resistor"}
    s["07 12V Out 2"]={"SSS2 setting":46,"State":False,"Label":"Connect +12V to Port 11 (J24:11)"}
    s["08 12V Out 1"]={"SSS2 setting":45,"State":False,"Label":"Connect +12V to Port 27 (J18:10)"}
    s["09 Ground Out 1"]={"SSS2 setting":47,"State":False,"Label":"Connect Ground to Port 17 (J18:1)"}
    s["10 Ground Out 2"]={"SSS2 setting":47,"State":False,"Label":"Connect Ground to Port 12 (J24:12)"}
    s["05 LIN to SHLD"]={"SSS2 setting":71,"State":False,"Label":"Connect LIN to Round Pin E (J10:5)"}
    s["06 LIN to Port 16"]={"SSS2 setting":72,"State":False,"Label":"Connect LIN to Port 16 (J24:16)"}
    
    

    settings["CAN"]={"Preprogrammed":{},"Custom":{}}
    t=settings["CAN"]["Preprogrammed"]
    t["08FF0001"]={"Transmit":True,"Application":"Detroit Diesel Message from MCM to CPC"} 
    t["08FF0003"]={"Transmit":True,"Application":""}
    t["08FF0103"]={"Transmit":True,"Application":""}
    t["08FF0203"]={"Transmit":True,"Application":""}
    t["08FF0303"]={"Transmit":True,"Application":""}
    t["08FF0603"]={"Transmit":True,"Application":""}
    t["08FF0703"]={"Transmit":True,"Application":""}
    t["0CFF0703"]={"Transmit":True,"Application":""}
    t["0CFE6E0B"]={"Transmit":True,"Application":""}
    t["10FF0903"]={"Transmit":True,"Application":""}
    t["18F00131"]={"Transmit":True,"Application":""}
    t["18F0010B"]={"Transmit":True,"Application":""}
    t["18FEF117"]={"Transmit":True,"Application":""}
    t["18FEF128"]={"Transmit":True,"Application":""}
    t["18FEF121"]={"Transmit":True,"Application":""}
    t["18FEF131"]={"Transmit":True,"Application":""}
    t["18E00017"]={"Transmit":True,"Application":""}
    t["18E00019"]={"Transmit":True,"Application":""}
    t["18E00021"]={"Transmit":True,"Application":""}
    t["18E00028"]={"Transmit":True,"Application":""}
    t["18E00031"]={"Transmit":True,"Application":""}
    t["10ECFF3D"]={"Transmit":True,"Application":""}
    t["10ECFF01"]={"Transmit":True,"Application":""}
    t["18FEF803"]={"Transmit":True,"Application":""}
    t["18FEF521"]={"Transmit":True,"Application":""}
    t["18FEF017"]={"Transmit":True,"Application":""}
    t["18FEF021"]={"Transmit":True,"Application":""}
    t["18FEF028"]={"Transmit":True,"Application":""}
    t["18DF00F9"]={"Transmit":True,"Application":""}
    t["18DFFFF9"]={"Transmit":True,"Application":""}
    t["0CF00203"]={"Transmit":True,"Application":""}
    t["18F00503"]={"Transmit":True,"Application":""}
    
    c=settings["CAN"]["Custom"]={}
    c["Example"]={"Major Period":1000,"Minor Period":5,"Transmit":True,"Messages":[]}
    m=c["Example"]["Messages"]
    m.append({"ID":"18FEF125","DLC":8,"Data":[0xD,0xE,0xA,0xD,0xB,0xE,0xE,0xF]})
    m.append({"ID":"18FEF125","DLC":8,"Data":[0xF,0xE,0xA,0xD,0xB,0xE,0xE,0xF]})
                  
    #print(settings)
    return settings

if __name__ == '__main__':
    settings=get_default_settings()
    with open('SSS2defaults.json','w') as outfile:
        json.dump(settings,outfile,indent=4)
    
