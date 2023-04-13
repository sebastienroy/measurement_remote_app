# Multisensor remote application

The goal of this application is to be used as remote application to gather detail results from the multisensor version of the Baby Shutter Tester tool.  
The Multisensor Baby Shutter Tester tool is used to measure both shutter speed (i.e. open time of the shutter of film camera) and shutter translation velocity. This later data are necessary for camera repairers to adjust the tension of springs used to move the shutter at the recommended speed.  

Camera repairers may be intersted with the global result, i.e. the translation time of the first and second shutter on the whole film frame, but may be also interested with the detailed results or even the measurement raw data.  

This is the global philosophy of the tool : allow the user of the Multisensor Baby Shutter Tester to gather both synthetic and detailed result of measurements of the shutter speed of the tested camera.  
The user is then able to export  data in any datasheet application and perform further processing or archivation processus.

# Interface Requirement
- The application shall be able to read measurement data stream that follows json format with content such as following:
```
    {
    'eventType': 'tbd', 
    [tbd] 
    }
```
