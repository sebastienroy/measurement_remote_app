# measurement_remote_app
An application that reads and displays the measurement values of a remote tool.

# Context
The idea of the project is to work in collaboration with measurement tools such as the Baby Shutter Tester

# Interface requirements
- The application shall be able to read measurements events data from a remote tool, using the USB interface.  
- The application shall be able to read measurement data stream that follows json format with content such as following:

    {
    "eventType": "shutterOpenTime",
    "value": 12.345,
    "unit": "millisecond"
    }
    
# Minimum Valuable Product (MVP)
- The application is able to connect to a remote tool through USB port and read the measurements stream
- The application is able to gather lists of measurements and display them
- The user is able to export lists of measure into main spreadsheet applications
- The user is able to delete a single measure
- The user is able to clear all the measures
