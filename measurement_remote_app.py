""" 
    This tool is intended to be interfaced with measurement tools such as the Baby Shutter Tester.
    The value of such an application is to help the user to enter series of measurement values 
    into a spreadsheet application. 
    So that, the user will be easily able to make statistics, mean value, mean deviation and so on,
    and also make archives of the measurements results.
"""
__author__ = "Sebastien ROY"
__license__ = "GPL"
__version__ = "0.0.1"
__status__ = "Development"

import threading
import time
import queue
import json
import sys
from json import JSONDecodeError
from tkinter import *
from  tkinter import ttk
#from serial import *
import serial.tools.list_ports
from serial import SerialException
import datetime

# global variable are not very beautiful, but acceptable in a small application 
ws = Tk()
comque= queue.Queue()
document = []
measureId = 0
serialPort = None
serialPorts = {}
portName = ''
is_stopped = False
selectedPort = StringVar()
connectionStatusLabel = None
combo = None
DEBUG = False

def testMeasureThread():
    """ Test purpose:
        Test listener used as a mock for COM port listener 
    """
    global is_stopped
    index = 0
    currentId = 0
    entries = ['Tagada tsouin', 
        '{\"eventType\": \"shutterOpenTime\",\"value\": 1234, \"unit\": \"microsecond\"}', 
        'pof pof', 
        '{\"eventType\": \"shutterOpenTime\",\"value\": 567, \"unit\": \"microsecond\"}', 
        '{\"eventType\": \"shutterOpenTime\",\"value\": 876, \"unit\": \"microsecond\"}', 
        'a', 
        '{\"eventType\": \"shutterOpenTime\",\"value\": 76, \"unit\": \"microsecond\"}', 
        '{\"eventType\": \"shutterOpenTime\",\"value\": 543, \"unit\": \"microsecond\"}', 
        '{\"eventType\": \"shutterOpenTime\",\"value\": 210987, \"unit\": \"microsecond\"}', 
        '{\"eventType\": \"shutterOpenTime\",\"value\": 4210987, \"unit\": \"microsecond\"}', 
        '{\"eventType\": \"shutterOpenTime\",\"value\": 54210987, \"unit\": \"microsecond\"}', 
        ''] 
    while not is_stopped:
        try:
            data = json.loads(entries[index])
            # Put a data in the queue
            comque.put(data)
             # Generate an event in order to notify the GUI
            ws.event_generate('<<Measure>>', when='tail')       
        except JSONDecodeError:
            if(DEBUG):
                print("Not JSon : " + entries[index])
        except TclError:
            break  
        time.sleep(1)
        index += 1
        if (index>= len(entries)):
            index = 0


def openSerialPort(name):
    """ Open default serial port
        If no serial port name has been defined, open the first port available
    """
    global serialPort, serialPorts, portName, connectionStatusLabel
    if(portName == '--'):
        serialPort = None
    elif(name in serialPorts):
        serialPort = serialPorts[name]
    else:
        for info in serial.tools.list_ports.comports():
            if info.name == portName:
                connectionStatusLabel.set("Connecting...")
                serialPort = serial.Serial(info.device)
                if(serialPort.is_open):
                    serialPorts[portName] = serialPort   
                    if(DEBUG):
                        print("SerialPort : " + str(serialPort))       
     
def listSerialPorts():
    """ All is in the title
    """
    portNames= [info.name for info in serial.tools.list_ports.comports()]
    if not portNames:
        portNames.append("--")
    return portNames

def measureThread():
    """ This function is executed in a separated thread 
        When JSon data is read on the serial port,
        the function pushs a <<Measure>> event in a queue for the main thread
    """
    global portName, is_stopped, connectionStatusLabel, serialPort
    try:
        while not is_stopped:
            if(serialPort == None or serialPort.is_open == False):
                time.sleep(1)
                openSerialPort(portName)
                if(serialPort == None):
                    connectionStatusLabel.set("No connection")
                elif(serialPort.is_open): 
                    connectionStatusLabel.set("Connected") 
                else:
                    connectionStatusLabel.set("Disonnected")

            if(serialPort != None and serialPort.is_open):
                try:
                    line = serialPort.readline()
                    data = json.loads(line)
                    # Put a data in the queue
                    comque.put(data)
                    # Generate an event in order to notify the GUI
                    print("Processed data event : " + str(data))
                    ws.event_generate('<<Measure>>', when='tail')       
                except JSONDecodeError:
                    if(DEBUG):
                        print("Not formated data:" + str(line))
                except SerialException:
                    # Connection failed
                    connectionStatusLabel.set("Not connected")
                    serialPort = None
                    serialPorts.pop(portName)
                except TclError:
                    print("TclError occured")
                except TypeError:
                    print("TypeError occured")
                except Exception:
                    print("Other error occured")
    finally:
        if(DEBUG):
            print("Measurement worker ended")

def handleShutterOpenTimeEvent(data):
    """ Handler for shutterOpenTime event"""
    # compute derived data
    value = data['value']
    if value !=0:
        # assumes that the value is expressed using microsecond unit
        # speed is expressed as s-1
        speed = 1000000.0/value
    else:
        speed = -1
    data['speed'] = speed
    
    # append measurement data to the document
    document.append(data)
    # append new data in the table
    unit = data['unit']
    tree = ws.nametowidget("mainFrame.measureTable")
    item = tree.insert(parent='', index='end', iid=data['id'],text='', values=(str(data['id']),str(value),"{:0.1f}".format(speed)))
    tree.see(item)
    tree.pack()

def dataEvent(event):
    """ Dispatches the events received from the listener """
    global measureId
    # get event data
    data = comque.get()
    # add an identifier
    data['id'] = measureId
    measureId += 1
    
    # dispatch according to the type
    eventType = data['eventType']
    if(eventType == 'shutterOpenTime'):
        handleShutterOpenTimeEvent(data)
        # only one event type for the moment

def clearAll():
    """ Callback used to clear all entries """
    global measureId
    # Clear treeView table
    tree = ws.nametowidget("mainFrame.measureTable")
    tree.delete(*tree.get_children())
    # Clear document
    document.clear()
    # Reset counter
    measureId = 0

def string_out( rows, separator='\t', line_feed='\n'):
    """ Prepares a string to send to the clipboard. """
    out = []
    for row in rows:
        out.append( separator.join( row ))  # Use '\t' (tab) as column seperator.
    return line_feed.join(out)              # Use '\n' (newline) as row seperator.

def documentToLists():
    """ Copy data to clipboard purpose:
        Get the document data and metadata into a list of lists (rows/columns)
    """
    data = []
    # Metadata
    data.append(["Baby Shutter Tester data exported using Measurement Remote Application"])
    data.append(["https://github.com/sebastienroy/measurement_remote_app"])
    data.append(["Date :", str(datetime.datetime.now())])
    # Columns header
    data.append(["Id", "Time (microseconds)", "Speed (1/s)"])
    # Data
    for row in document:
        data.append([str(row['id']), str(row['value']), str(row['speed'])])        
    return data
    
def copyToClipboard():
    """ Copies all metadata and data to the clipboard. """
    data = documentToLists()
    ws.clipboard_clear()
    ws.clipboard_append(string_out(data, separator='\t'))     # Paste string to the clipboard
    ws.update()   # The string stays on the clipboard after the window is closed
    
def on_closing():
    """ Close ports, exit threads... """
    global is_stopped
    is_stopped = True
    ws.destroy()
    if serialPort and serialPort.is_open:
        serialPort.close()
    sys.exit()

def on_combo_selection(event):
    """ COM port selection Callback """
    global portName
    portName = selectedPort.get()
    if(DEBUG):
        print("Change port to : " + portName)
    openSerialPort(portName)    

def update_cb_list():
    global combo
    combo['values'] = listSerialPorts()

def main():
    """ defining a main function is not necessary but cleaner """
    
    global portName, connectionStatusLabel, combo

    ws.protocol("WM_DELETE_WINDOW", on_closing)
    ws.title("Measurement Remote Application")
    ws.geometry("550x200")	
    frame = Frame(ws, name="mainFrame")
    frame.pack(expand=True, fill='both')

    #scrollbar
    v_scroll = Scrollbar(frame, name = "v_scroll")
    
    # Button_fram is necessary to put many buttons in a row
    button_frame = Frame(frame, name="buttonFrame")
    button_frame.pack(expand=True, fill='both')

    Button(button_frame, text="Clear all", command=clearAll).grid(row=0, column=0, padx=5, pady=5)
    Button(button_frame, text="Copy to Clipboard", command=copyToClipboard).grid(row=0, column=1, padx=5, pady=5)
    Label(button_frame, text="Device :").grid(row=0, column=2, padx=5, pady=5)
    combo = ttk.Combobox(button_frame, textvariable = selectedPort, state='readonly', width=8,  postcommand = update_cb_list)
    ports=listSerialPorts()
    portName = ports[0]
    combo['values']=ports
    combo.current(0)
    combo.bind("<<ComboboxSelected>>", on_combo_selection)
    combo.grid(row=0, column=3, padx=5, pady=5)
    
    connectionStatusLabel = StringVar(frame, "Unknown Status")
    Label(button_frame, textvariable=connectionStatusLabel).grid(row=0, column=4, padx=5, pady=5)

    tree = ttk.Treeview(frame, name = "measureTable")
    tree.config(yscrollcommand=v_scroll.set)
    v_scroll.pack(side=RIGHT, fill=Y)
    
    tree['columns'] = ('id', 'duration', 'speed')

    tree.column("#0", width=0,  stretch=NO)
    tree.column("id",anchor=CENTER, width=80, stretch = YES)
    tree.column("duration",anchor=CENTER,width=120, stretch = YES)
    tree.column("speed",anchor=CENTER,width=160, stretch = YES)

    tree.heading("#0",text="",anchor=CENTER)
    tree.heading("id",text="Id",anchor=CENTER)
    tree.heading("duration",text="Time (microseconds)",anchor=CENTER)
    tree.heading("speed",text="Speed (1/s)",anchor=CENTER)
    
    tree.pack(expand=True, fill='both', padx=2, pady=2)
    v_scroll.config(command=tree.yview)

    # start event pump
    ws.bind('<<Measure>>', dataEvent)

    # TEST : change the thread to start in order to generate test data
    #Thr=threading.Thread(target=testMeasureThread)
    Thr=threading.Thread(target=measureThread)
    Thr.start()

    ws.mainloop()

if __name__ == "__main__":    
    main()
