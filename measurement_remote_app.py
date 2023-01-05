import threading
import time
import queue
import json
from json import JSONDecodeError
from tkinter import *
from  tkinter import ttk
import serial.tools.list_ports

ws = Tk()
comque= queue.Queue()
clcvar = StringVar()
document = []
measureId = 0

def testMeasureThread():
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

def handleShutterOpenTimeEvent(data):
    # compute derived data
    value = data['value']
    if value !=0:
        speed = 1000000.0/value
    else:
        speed = NaN
    data['speed'] = speed
    
    # append measurement data to the document
    document.append(data)
    # append new data in the table
    unit = data['unit']
    #clcvar.set(str(comque.get()))
    #clcvar.set(eventType + ';' + str(value) + ';' + unit)
    tree = ws.nametowidget("mainFrame.measureTable")
    item = tree.insert(parent='', index='end', iid=data['id'],text='', values=(str(data['id']),str(value),str(speed)))
    tree.see(item)
    tree.pack()

    
            
def dataEvent(event):
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
    print("All lines cleared")

def main():

    # test on COM ports
    # Needs : pip install pyserial
    ports = []
    for port in serial.tools.list_ports.comports():
        ports.append(port.name)
    print(ports)

    ws.title("Measurement Remote Application")
    ws.geometry("400x200")	
    frame = Frame(ws, name="mainFrame")
    frame.pack(expand=True, fill='both')
    
    #scrollbar
    v_scroll = Scrollbar(frame, name = "v_scroll")
    v_scroll.pack(side=RIGHT, fill=Y)
    
    # There is something to do here to put many buttons in a row
    #Label(frame, textvariable=clcvar, width=50).pack(pady=10)
    Button(frame, text="Clear all", command=clearAll).pack(pady=10, anchor=W, ipadx=10)

    tree = ttk.Treeview(frame, yscrollcommand=v_scroll.set, name = "measureTable")
    tree['columns'] = ('id', 'duration', 'speed')

    tree.column("#0", width=0,  stretch=NO)
    tree.column("id",anchor=CENTER, width=80, stretch = YES)
    tree.column("duration",anchor=CENTER,width=120, stretch = YES)
    tree.column("speed",anchor=CENTER,width=160, stretch = YES)

    tree.heading("#0",text="",anchor=CENTER)
    tree.heading("id",text="Id",anchor=CENTER)
    tree.heading("duration",text="Time (microseconds)",anchor=CENTER)
    tree.heading("speed",text="Speed (1/s)",anchor=CENTER)
    
    tree.pack(expand=True, fill='both')
    v_scroll.config(command=tree.yview)

    # start event pump
    ws.bind('<<Measure>>', dataEvent)

    Thr=threading.Thread(target=testMeasureThread)
    Thr.start()

    ws.mainloop()
    
main()

