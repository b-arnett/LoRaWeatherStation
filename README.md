# LoRaWeatherStation
## Raspberry Pi Pico 2 based, automated solar-powered weather station and 'smart' home.

This repository contains code, STL cad files, notes, and pictures for a Remote weather station and 'smart' home that I designed.  This project uses RYLR993 lite LoRa modules for the communication methodbetween the weather station and model house.  The use of these modules is pretty simple with the use of AT+ commands and initial range tests showed 1000+ feet in urban environment, and easily over 1 mile in rural environment.   

## Repo 'map'
- CAD folder contains STL files for both Weather Station and Smart Home
- WeatherStation folder contains all code associated with the Weather Station.  WSMainSend.py is the finalized, tested and working code.  Other files are test programs.
- SmartHouse folder contains all code associated with the Smart House.  ModelComplete.py is the finalized, tested and working code.  Other files are test programs.
- LoRaTests folder contains test code for the RYLR993 lite lora modules.
- Documents contains pictures, notebook scans, and other documentation accumulated during this projects development.

