import threading
import time
import queue
import json
from json import JSONDecodeError
from tkinter import *
from  tkinter import ttk

ws = Tk()
comque= queue.Queue()
clcvar = StringVar()
document = []

def testMeasureThread():
    index = 0
    currentId = 0
    entries = ['Tagada tsouin', '{\"eventType\": \"shutterOpenTime\",\"value\": 1234, \"unit\": \"microsecond\"}', 'pof pof', '{\"eventType\": \"shutterOpenTime\",\"value\": 567, \"unit\": \"microsecond\"}', 'Et voila', 'Tiens donc', 'a', 'b'] 
    while 1:
        try:
            data = json.loads(entries[index])
            data["id"] = currentId
            currentId += 1
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


            
def measureEvent(event):

    data = comque.get()
    # append measurement data to the document
    document.append(data)
    # append new data in the table
    id = data['id']
    eventType = data['eventType']
    value = data['value']
    unit = data['unit']
    #clcvar.set(str(comque.get()))
    clcvar.set(eventType + ';' + str(value) + ';' + unit)
    tree = ws.nametowidget("mainFrame.measureTable")
    tree.insert(parent='', index='end', iid=id,text='', values=(eventType,str(value),unit))
    tree.pack()
    
    

def main():
    ws.title("Measurement Remote Application")
    ws.geometry("500x200")	
    frame = Frame(ws, name="mainFrame")
    frame.pack()
    
    #scrollbar
    v_scroll = Scrollbar(frame)
    v_scroll.pack(side=RIGHT, fill=Y)
     
    Label(frame, textvariable=clcvar, width=50).pack(pady=10)
    ws.bind('<<Measure>>', measureEvent)
    
    tree = ttk.Treeview(frame, yscrollcommand=v_scroll.set, name = "measureTable")
    tree['columns'] = ('measure_type', 'value', 'unit')

    tree.column("#0", width=0,  stretch=NO)
    tree.column("measure_type",anchor=CENTER, width=80)
    tree.column("value",anchor=CENTER,width=80)
    tree.column("unit",anchor=CENTER,width=80)

    tree.heading("#0",text="",anchor=CENTER)
    tree.heading("measure_type",text="Measure Type",anchor=CENTER)
    tree.heading("value",text="Value",anchor=CENTER)
    tree.heading("unit",text="Unit",anchor=CENTER)
    
    tree.pack()
    v_scroll.config(command=tree.yview)

    Thr=threading.Thread(target=testMeasureThread)
    Thr.start()

    ws.mainloop()
    
main()




