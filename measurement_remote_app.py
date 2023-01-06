import threading
import time
import queue
import json
from json import JSONDecodeError
from tkinter import *
from  tkinter import ttk
import serial.tools.list_ports
from serial import SerialException
import datetime

# global variable are not very beautiful, but acceptable in a small application 
ws = Tk()
comque= queue.Queue()
document = []
measureId = 0
serialPort = None
portName = ''

def testMeasureThread():
    """ Test listener used as a mock for COM port listener """
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
    while 1:
        try:
            data = json.loads(entries[index])
            # Put a data in the queue
            comque.put(data)
             # Generate an event in order to notify the GUI
            ws.event_generate('<<Measure>>', when='tail')       
        except JSONDecodeError:
            print("JSONDecodeError:" + entries[index])
        except TclError:
            break  
        time.sleep(1)
        index += 1
        if (index>= len(entries)):
            index = 0

def openSerialPort():
    """ Open default serial port
        If no serial port name has been defined, open the first port available
    """
    global serialPort, portName
    ports = serial.tools.list_ports.comports()
    if(len(ports) > 0):
        serialPort = serial.Serial(ports[0].name)
        portName = serialPort.name

def measureThread():
    while 1:
        if(serialPort == None or serialPort.is_open == False):
            time.sleep(1)
            openSerialPort()
        if(serialPort != None and serialPort.is_open):
            line = serialPort.readline()
            try:
                data = json.loads(line)
                # Put a data in the queue
                comque.put(data)
                # Generate an event in order to notify the GUI
                ws.event_generate('<<Measure>>', when='tail')       
            except JSONDecodeError:
                print("JSONDecodeError:" + str(line))
            except SerialException:
                print("Communication error")
            except TclError:
                break  


def handleShutterOpenTimeEvent(data):
    """ Handler for shutterOpenTime event"""
    # compute derived data
    value = data['value']
    if value !=0:
        # assumes that the value is expressed using microsecond unit
        # speed is expressed as s-1
        speed = 1000000.0/value
    else:
        speed = 'NaN'
    data['speed'] = speed
    
    # append measurement data to the document
    document.append(data)
    # append new data in the table
    unit = data['unit']
    tree = ws.nametowidget("mainFrame.measureTable")
    item = tree.insert(parent='', index='end', iid=data['id'],text='', values=(str(data['id']),str(value),str(speed)))
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
    """ Get the document data and metadata into a list of lists (rows/columns)"""
    data = []
    # Metadata
    temp = []
    temp.append("Baby Shutter Tester data exported from Measurement Remote Application")
    data.append(temp)
    temp = []
    temp.append("https://github.com/sebastienroy/measurement_remote_app")
    data.append(temp)
    temp = []
    temp.append("Date :")
    temp.append(str(datetime.datetime.now()))
    data.append(temp)
    # Columns header
    headers = []
    headers.append("Id")
    headers.append("Time (microseconds)")
    headers.append("Speed (1/s)")
    data.append(headers)
    
    for row in document:
        temp = []
        temp.append(str(row['id']))
        temp.append(str(row['value']))
        temp.append(str(row['speed']))
        data.append(temp)
        
    return data
    
def copyToClipboard():
    """ Copies all metadata and data to the clipboard. """
    data = documentToLists()
    ws.clipboard_clear()
    ws.clipboard_append(string_out(data, separator='\t'))     # Paste string to the clipboard
    ws.update()   # The string stays on the clipboard after the window is closed

def configureDlg():
    """ Allows the user to confure the communication port"""
    print("ConfigureDlg() called")

def main():
    """ defining a main function is not necessary but cleaner """

    # test on COM ports
    # Needs : pip install pyserial
    ports = []
    for port in serial.tools.list_ports.comports():
        print(port)
        ports.append(port.name)
    print(ports)

    ws.title("Measurement Remote Application")
    ws.geometry("400x200")	
    frame = Frame(ws, name="mainFrame")
    frame.pack(expand=True, fill='both')

    #scrollbar
    v_scroll = Scrollbar(frame, name = "v_scroll")
    
    # There is something to do here to put many buttons in a row
    button_frame = Frame(frame, name="buttonFrame")
    button_frame.pack(expand=True, fill='both')

    Button(button_frame, text="Clear all", command=clearAll).grid(row=0, column=0, padx=5, pady=5)
    Button(button_frame, text="Copy to Clipboard", command=copyToClipboard).grid(row=0, column=1, padx=5, pady=5)

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

    #Thr=threading.Thread(target=testMeasureThread)
    Thr=threading.Thread(target=measureThread)
    Thr.start()

    ws.mainloop()
    
main()
