# Multisensor remote application

The goal of this application is to be used as remote application to gather detail results from the multisensor version of the Baby Shutter Tester tool.  
The Multisensor Baby Shutter Tester tool is used to measure both shutter speed (i.e. open time of the shutter of film camera) and shutter translation velocity. This later data are necessary for camera repairers to adjust the tension of springs used to move the shutter at the recommended speed.  

Camera repairers may be intersted with the global result, i.e. the translation time of the first and second shutter on the whole film frame, but may be also interested with the detailed results or even the measurement raw data.  

This is the global philosophy of the tool : allow the user of the Multisensor Baby Shutter Tester to gather both synthetic and detailed result of measurements of the shutter speed of the tested camera.  
The user is then able to export  data in any datasheet application and perform further processing or archivation processus.

## Interface Requirement

- The application shall be able to read measurement data stream that follows json format with content such as following:
- The application shall interpret the negative values as missing value (event not detected)

```json
    {
    'eventType': 'MultiSensorMeasure', 
    'unit': 'microsecond', 
    'firmware_version': '1.0.0',
    'bottomLeftOpen': 0,
    'bottomLeftClose': 987,
    'centerOpen': 3456,
    'centerClose': 4567,
    'topRightOpen': 5678,
    'topRightClose': 6789
    }
```

## Displayed requirements

- The application shall display to the user both processed data and raw data.  
  
- Global data  
  - speed (central) = 1000/(centerClose-centerOpen)
  - Exposure (central) = (centerClose-centerOpen)/1000
  - 1st shutter course = abs(topRightOpen - bottomLeftOpen)
  - 1st shutter course extrapolation to full frame
  - 2nd shutter course = abs(topRightClose - bottomLeftClose)
  - 2nd shutter course extrapolation to full frame  
  
- Detailed data  
  - Speed and exposure at bottomLeft and topRight corners
  - half cours of 1st and 2nd shutters
