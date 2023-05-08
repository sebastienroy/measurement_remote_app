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
from dataclasses import dataclass

is_stopped = False
DEBUG = True
app = None


def testMeasureThread():
    """ Test purpose:
        Test listener used as a mock for COM port listener 
    """
    global app, is_stopped
    index = 0
    currentId = 0
    entries = ['Tagada tsouin', 
        '{\"eventType\": \"MultiSensorMeasure\", \"unit\": \"microsecond\", \"firmware_version\": \"1.0.0\", \"bottomLeftOpen\": 0, \"bottomLeftClose\": 987, \"centerOpen\": 3456, \"centerClose\": 4567, \"topRightOpen\": 5678, \"topRightClose\": 6789}', 
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
            app.comque.put(data)
            # Generate an event in order to notify the GUI
            app.ws.event_generate('<<Measure>>', when='tail')       
        except JSONDecodeError:
            if(DEBUG):
                print("Not JSon : " + entries[index])
        except TclError:
            break  
        time.sleep(1)
        index += 1
        if (index>= len(entries)):
            index = 0

def measureThread():
    """ This function is executed in a separated thread 
        When JSon data is read on the serial port,
        the function pushs a <<Measure>> event in a queue for the main thread
    """
    global app, is_stopped
    try:
        while not is_stopped:
            if(app.serialPort == None or app.serialPort.is_open == False):
                time.sleep(1)
                app.openSerialPort(app.portName)
                if(app.serialPort == None):
                    app.connectionStatusLabel.set("No connection")
                elif(app.serialPort.is_open): 
                    app.connectionStatusLabel.set("Connected") 
                else:
                    app.connectionStatusLabel.set("Disonnected")

            if(app.serialPort != None and app.serialPort.is_open):
                try:
                    line = app.serialPort.readline()
                    if(DEBUG):
                        print(line)
                    data = json.loads(line)
                    # Put a data in the queue
                    app.comque.put(data)
                    # Generate an event in order to notify the GUI
                    print("Processed data event : " + str(data))
                    app.ws.event_generate('<<Measure>>', when='tail')       
                except JSONDecodeError:
                    if(DEBUG):
                        print("Not formated data:" + str(line))
                except SerialException:
                    # Connection failed
                    app.connectionStatusLabel.set("Not connected")
                    app.serialPort = None
                    app.serialPorts.pop(app.portName)
                except TclError:
                    print("TclError occured")
                except TypeError:
                    print("TypeError occured")
                except Exception:
                    print("Other error occured")
    finally:
        if(DEBUG):
            print("Measurement worker ended")
"""
    This class describes the data managed by the application
"""
@dataclass
class DataDef:
    id: str
    colLabel: str
    colWidth: int
    format: str
    formula: callable

    def strValue(self, value):
        if(type(value) == float):
            return self.format.format(value)
        else:
            return str(value)

'''
    Computes speed in 1/s from microseconds 
    a data < 0 mean no value
'''
def microSpeed(val1, val2):
    if((val1 == val2) or (val1 < 0) or (val2 < 0)):
        return "-"
    else:
        return abs(1000000.0/(val1-val2))

'''
    Computes the time difference in ms from microseconds
    a data < 0 mean no value
'''   
def microTime(val1, val2):
    if((val1 < 0) or (val2 < 0)):
        return "-"
    else:
        return abs((val1-val2)/1000.0)

def extrapolate(val):
    global app
    if(type(val) == float):
        return val * app.extrapolation_factor
    else:
        return val


class RemoteApp:

    def __init__(self):        
        self.ws = Tk()
        self.comque= queue.Queue()
        self.document = []
        self.measureId = 0
        self.serialPort = None
        self.serialPorts = {}
        self.portName = ''
        self.is_stopped = False
        self.selectedPort = StringVar()
        self.connectionStatusLabel = None
        self.combo = None
        self.selectedDirection = StringVar()
        self.extrapolation_factor = 24.0 / 20.0 # extrapolation from 20mm to 24mm (vertical direction)

        # This is the columns definition : column and data id, column name, column width, value format, value computation using json data
        self.dataDefs = [
            DataDef('id', 'Id', 20, '{}', lambda data: data['id']),
            DataDef('speed_c', 'Speed (1/s)', 60, '{:0.1f}', lambda data: microSpeed(data['centerClose'], data['centerOpen'])),
            DataDef('time_c', 'Time (ms)', 60, '{:0.3f}', lambda data: microTime(data['centerClose'], data['centerOpen'])),
            DataDef('course_1', 'Open (ms)', 60, '{:0.2f}', lambda data: microTime(data['topRightOpen'], data['bottomLeftOpen'])),
            DataDef('course_2', 'Close (ms)', 60, '{:0.2f}', lambda data: microTime(data['topRightClose'], data['bottomLeftClose'])),
            DataDef('course_1_ext', 'Open ext', 60, '{:0.2f}', lambda data: extrapolate(data['course_1'])),
            DataDef('course_2_ext', 'Close ext', 60, '{:0.2f}', lambda data: extrapolate(data['course_2'])),
            DataDef('speed_bl', 'Speed Bot. L.', 70, '{:0.1f}', lambda data: microSpeed(data['bottomLeftClose'], data['bottomLeftOpen'])),
            DataDef('time_bl', 'Time Bot. L.', 70, '{:0.3f}', lambda data: microTime(data['bottomLeftClose'], data['bottomLeftOpen'])),
            DataDef('speed_tr', 'Speed Top R.', 70, '{:0.1f}', lambda data: microSpeed(data['topRightClose'], data['topRightOpen'])),
            DataDef('time_tr', 'Time Top R.', 70, '{:0.3f}', lambda data: microTime(data['topRightClose'], data['topRightOpen'])),
            DataDef('course_1_12', 'Open 1/2', 60, '{:0.2f}', lambda data: microTime(data['centerOpen'], data['bottomLeftOpen'])),
            DataDef('course_1_22', 'Open 2/2', 60, '{:0.2f}', lambda data: microTime(data['centerOpen'], data['topRightOpen'])),
            DataDef('course_2_12', 'Close 1/2', 60, '{:0.2f}', lambda data: microTime(data['centerClose'], data['bottomLeftClose'])),
            DataDef('course_2_22', 'Close 2/2', 60, '{:0.2f}', lambda data: microTime(data['centerClose'], data['topRightClose']))
            ]

    def openSerialPort(self, name):
        """ Open default serial port
            If no serial port name has been defined, open the first port available
        """
        #global serialPort, serialPorts, portName, connectionStatusLabel
        global app

        if(self.portName == '--'):
            self.serialPort = None
        elif(name in self.serialPorts):
            self.serialPort = self.serialPorts[name]
        else:
            for info in serial.tools.list_ports.comports():
                if info.name == self.portName:
                    app.connectionStatusLabel.set("Connecting...")
                    self.serialPort = serial.Serial(info.device)
                    if(self.serialPort.is_open):
                        self.serialPorts[app.portName] = self.serialPort   
                        if(DEBUG):
                            print("SerialPort : " + str(app.serialPort))       
     
    def listSerialPorts(self):
        """ All is in the title
        """
        portNames= [info.name for info in serial.tools.list_ports.comports()]
        if not portNames:
            portNames.append("--")
        return portNames


    def handleMultiSensorMeasure(self, data):
        for dataDef in self.dataDefs:
            data[dataDef.id] = dataDef.formula(data)
 
        self.document.append(data)
        tree = self.ws.nametowidget("mainFrame.measureTable")
        # iterate on all definitions, get the value that is stored with the defined id and get it as string
        rowValues = [(dataDef.strValue(data[dataDef.id])) for dataDef in self.dataDefs]
        item = tree.insert(parent='', index='end', iid=data['id'],text='', values=rowValues)


    def dataEvent(self, event):
        """ Dispatches the events received from the listener """
        # get event data
        data = self.comque.get()
        # add an identifier
        data['id'] = self.measureId
        self.measureId += 1
        
        # dispatch according to the type
        eventType = data['eventType']
        if(eventType == 'MultiSensorMeasure'):
            self.handleMultiSensorMeasure(data)

    def clearAll(self):
        """ Callback used to clear all entries """
        # Clear treeView table
        tree = self.ws.nametowidget("mainFrame.measureTable")
        tree.delete(*tree.get_children())
        # Clear document
        self.document.clear()
        # Reset counter
        self.measureId = 0

    def string_out(self, rows, separator='\t', line_feed='\n'):
        """ Prepares a string to send to the clipboard. """
        out = []
        for row in rows:
            out.append( separator.join( row ))  # Use '\t' (tab) as column seperator.
        return line_feed.join(out)              # Use '\n' (newline) as row seperator.

    def documentToLists(self):
        """ Copy data to clipboard purpose:
            Get the document data and metadata into a list of lists (rows/columns)
        """
        data = []
        # Metadata
        data.append(["Shutter Lover data exported using Remote Application"])
        data.append(["https://github.com/sebastienroy/measurement_remote_app"])
        data.append(["Date :", str(datetime.datetime.now())])
        # Columns header
        headers = [ (dataDef.colLabel) for dataDef in self.dataDefs]
        data.append(headers)
        # Data
        for row in self.document:
            rowValues = [(dataDef.strValue(row[dataDef.id])) for dataDef in self.dataDefs]
            data.append(rowValues)
        return data
    
    def copyToClipboard(self):
        """ Copies all metadata and data to the clipboard. """
        data = self.documentToLists()
        self.ws.clipboard_clear()
        self.ws.clipboard_append(self.string_out(data, separator='\t'))     # Paste string to the clipboard
        self.ws.update()   # The string stays on the clipboard after the window is closed
        
    def on_closing(self):
        """ Close ports, exit threads... """
        global is_stopped
        is_stopped = True
        self.ws.destroy()
        if self.serialPort and self.serialPort.is_open:
            self.serialPort.close()
        sys.exit()

    def on_combo_selection(self, event):
        """ COM port selection Callback """
        
        self.portName = self.selectedPort.get()
        if(DEBUG):
            print("Change port to : " + self.portName)
        self.openSerialPort(self.portName)  

    def update_cb_list(self):
        self.combo['values'] = self.listSerialPorts()

    def on_direction_selection(self, event):
        if(self.selectedDirection.get() == "Vertical"):
            self.extrapolation_factor = 24.0 / 20.0
        else:
            self.extrapolation_factor = 36.0 / 32.0
        print("Selected Direction: {}, extrapolation factor = {}".format(self.selectedDirection.get(), self.extrapolation_factor) )

    def run(self):
        self.ws.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.ws.title("Shutter Lover Remote Application")
        self.ws.geometry("1024x200")	
        frame = Frame(self.ws, name="mainFrame")
        frame.pack(expand=True, fill='both')

        #scrollbar
        v_scroll = Scrollbar(frame, name = "v_scroll")
        
        # Button_frame is necessary to put many buttons in a row
        button_frame = Frame(frame, name="buttonFrame")
        button_frame.pack(expand=True, fill='both')

        Button(button_frame, text="Clear all", command=self.clearAll).grid(row=0, column=0, padx=5, pady=5)
        Button(button_frame, text="Copy to Clipboard", command=self.copyToClipboard).grid(row=0, column=1, padx=5, pady=5)

        # Connection
        ttk.Separator(master=button_frame, orient=VERTICAL, style='TSeparator', class_= ttk.Separator,takefocus= 0).grid(row=0, column=2, padx=5, pady=0)
        Label(button_frame, text="Device :").grid(row=0, column=3, padx=5, pady=5)
        # serial ports combo
        self.combo = ttk.Combobox(button_frame, textvariable = self.selectedPort, state='readonly', width=8,  postcommand = self.update_cb_list)
        self.ports=self.listSerialPorts()
        self.portName = self.ports[0]
        self.combo['values']=self.ports
        self.combo.current(0)
        self.combo.bind("<<ComboboxSelected>>", self.on_combo_selection)
        self.combo.grid(row=0, column=4, padx=5, pady=5)
        
        # serial port status
        self.connectionStatusLabel = StringVar(frame, "Unknown Status")
        Label(button_frame, textvariable=self.connectionStatusLabel).grid(row=0, column=5, padx=5, pady=5)

        # curtain translation direction combo
        ttk.Separator(master=button_frame, orient=VERTICAL, style='TSeparator', class_= ttk.Separator,takefocus= 0).grid(row=0, column=6, padx=5, pady=0)
        Label(button_frame, text="Curtain translation direction :").grid(row=0, column=7, padx=7, pady=5)
        directionCombo = ttk.Combobox(button_frame, values=['Vertical', 'Horizontal'], textvariable = self.selectedDirection, state='readonly', width=8,  postcommand = self.update_cb_list)
        directionCombo.current(0)
        directionCombo.bind("<<ComboboxSelected>>", self.on_direction_selection)
        directionCombo.grid(row=0, column=8, padx=5, pady=5)

        tree = ttk.Treeview(frame, name = "measureTable")
        tree.config(yscrollcommand=v_scroll.set)
        v_scroll.pack(side=RIGHT, fill=Y)
        
        tree['columns'] = [(dataDef.id) for dataDef in self.dataDefs]

        tree.column("#0", width=0,  stretch=NO)
        for dataDef in self.dataDefs:
            tree.column(dataDef.id, anchor=CENTER, width=dataDef.colWidth, stretch = YES)    

        tree.heading("#0",text="",anchor=CENTER)
        for dataDef in self.dataDefs:
            tree.heading(dataDef.id, text=dataDef.colLabel, anchor=CENTER)

        tree.pack(expand=True, fill='both', padx=2, pady=2)
        v_scroll.config(command=tree.yview)

        # start event pump
        self.ws.bind('<<Measure>>', self.dataEvent)

        # TEST : change the thread to start in order to generate test data
        #Thr=threading.Thread(target=testMeasureThread)
        Thr=threading.Thread(target=measureThread)
        Thr.start()

        self.ws.mainloop()

if __name__ == "__main__":   
    app = RemoteApp()
    app.run()
