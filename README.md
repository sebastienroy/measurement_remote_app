# measurement_remote_app
An application that reads and displays the measurement values of a remote tool.

# Context
The idea of the project is to create an application that can be interfaced with measurement tools such as the Baby Shutter Tester.  
The value of such an application is to help the user to enter series of measurement values into a spreadsheet application.
So that, the user will be easily able to make statistics, mean value, mean deviation and so on, and also make archives of the measurements results.

# Interface requirements
- The application shall be able to read measurements events data from a remote tool, using the USB interface as a serial data interface.  
- The application shall be able to read measurement data stream that follows json format with content such as following:
```
    {
    "eventType": "shutterOpenTime",
    "value": 1234,
    "unit": "microsecond",
    "calibration": -48
    }
 ```
 *NB: the data are streamed in a single line, each of them separated by LINE_FEED characters. The above example is represented multiline for readability purpose* 
 - The application shall ignore data from the stream that is not in json format
 - The application shall ignore data from the stream that contains no relevant or incomplete information
# Minimum Valuable Product (MVP)
- The application is able to connect to a remote tool through USB port and read the measurements stream
- The application is able to gather lists of measurements and display them
- The user is able to export lists of measures into main spreadsheet applications
- The user is able to clear all the measures

# Non functional requirements
The non fonctional requirements that drive architectural design are the following:
- Cross-platform : the application may be executed on Windows, Mac and Linux operating systems, on x86 and Raspberry Pi platforms
- Open source : the user may be able to extend the application for his specific needs. The chosen technologies must be easy to read, understand and extend by a medium skilled developper.

# Technical design
- Language is Python3 : mainstream language, interpreted -> easy to develop
- GUI technology : TkInter (no need of additional libraries) -> easy to deploy
- Design pattern Model View Controler (MVC): robustness, modularity -> easy to extend
