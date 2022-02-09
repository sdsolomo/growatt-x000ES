#!/usr/bin/env python3

import time
import datetime
import os
import sys
from pymodbus.exceptions import ModbusIOException
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from influxdb import InfluxDBClient

influxhost = "127.0.0.1"
influxport = "8086"
influxdbname = "growatt"
influxuser = "None"
influxpass = "None"
influxmeasurement = "inverter"

interval = 60

numinverters = 1
inverterusbport1 = "/dev/ttyUSB0"
#not sure yet if the inverters will allow me to poll them over a single usb connection or not
inverterusbport2 = "/dev/ttyUSB1"
inverterusbport3 = "/dev/ttyUSB2"

verbose = 0
gwverbose = 0
gwinfodump = 1

# Codes
StatusCodes = {
    0: "Standby",
    1: "noUSE",
    2: "Discharge",
    3: "Fault",
    4: "Flash",
    5: "PV Charge",
    6: "AC Charge",
    7: "Combine Charge",
    8: "Combine charge and Bypass",
    9: "PV charge and Bypass",
    10: "AC Charge and Bypass",
    11: "Bypass",
    12: "PV charge and discharge"
}

def merge(*dict_args):
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result

class Growatt:
    def __init__(self, client, name, unit):
        self.client = client
        self.name = name
        self.unit = unit

        row = self.client.read_holding_registers(73, unit=self.unit)
        if type(row) is ModbusIOException:
            if gwverbose: print("GWVERBOSE1",row)
            raise row
        self.modbusVersion = row.registers[0]

    def read(self):
        row = self.client.read_input_registers(0, 83, unit=self.unit)
        if gwverbose: print("GWVERBOSE2")
        if gwverbose: print("GWVERBOSE3")
        info = {                                    # ==================================================================
            "Module": unit,
            "StatusCode": row.registers[0],         # N/A,      Inverter Status,    Inverter run state
            "Status": StatusCodes[row.registers[0]],
            "Vpv1": float(row.registers[1]) / 10,               # 0.1V,     PV1 voltage
            "Vpv2": float(row.registers[2]) / 10,               # 0.1V,     PV2 voltage
            "Ppv1H": float(row.registers[3]) / 10,              # 0.1W,     PV1 Charge power (high)
            "Ppv1L": float(row.registers[4]) / 10,              # 0.1W,     PV1 Charge power (low) 
            "Ppv2H": float(row.registers[5]) / 10,              # 0.1W,     PV2 Charge power (high)
            "Ppv2L": float(row.registers[6]) / 10,              # 0.1W,     PV2 Charge power (low)
            "Buck1Curr": float(row.registers[7]) / 10,          # 0.1A,     Buck1 current
            "Buck2Curr": float(row.registers[8]) / 10,          # 0.1A,     Buck2 current
            "OP_WattH": float(row.registers[9]) / 10,           # 0.1W,     Output active power (high)
            "OP_WattL": float(row.registers[10]) / 10,          # 0.1W,     Output active power (low)
            "OP_VAH": float(row.registers[11]) / 10,            # 0.1VA     Output apparent power (high)
            "OP_VAL": float(row.registers[12]) / 10,            #
            "ACChr_WattH": float(row.registers[13]) / 10,       # 0.1W,     AC Charge Watts (high)
            "ACChr_WattL": float(row.registers[14]) / 10,       #
            "ACChr_VAH": float(row.registers[15]) / 10,         # 0.1VA,    AC Charge apparent power (high)
            "ACChr_VAL": float(row.registers[16]) / 10,         #
            "Bat_Volt": float(row.registers[17]) / 100,         # 0.01V,    Battery Voltage
            "BatterySOC": float(row.registers[18]) / 1,         # 1%,       Battery State of Charge
            "BusVolt": float(row.registers[19]) / 10,           # 0.1V,     Bus Voltage
            "GridVolt": float(row.registers[20]) / 10,          # 0.1V,     AC input Voltage
            "LineFreq": float(row.registers[21]) / 100,         # 0.01Hz,   AC input Freq
            "OutputVolt": float(row.registers[22]) / 10,        # 0.1V,     AC Output Voltage
            "OutputFreq": float(row.registers[23]) / 100,       # 0.01Hz    AC Output Freq
            "OutputDCV": float(row.registers[24]) / 10,         # 0.1V      DC Output Voltage
            "InvTemp": float(row.registers[25]) / 10,           # 0.1C      Inverter Temp
            "DCDCTemp": float(row.registers[26]) / 10,          # 0.1C      DCDC Temp
            "LoadPercent": float(row.registers[27]) / 10,       # 0.1%      Inverter Load Percent
            "Bat_dspp_V": float(row.registers[28]) / 100,         # 0.01V     Battery-port volt (DSP)
            "Bat_dspb_V": float(row.registers[29]) / 100,         # 0.01V     Battery-bus voltage (DSP)
            "TimeTotalH": float(row.registers[30]) / 2,         # 0.5S,     Time total H,       Work time total (high)
            "TimeTotalL": float(row.registers[31]) / 2,         # 0.5S,     Time total L,       Work time total (low)
            "Buck1Temp": float(row.registers[32]) / 10,         # 0.1C,     Temperature,        Inverter temperature
            "Buck2Temp": float(row.registers[33]) / 10,         # 0.1C,     Temperature,        Inverter temperature
            "OP_Curr": float(row.registers[34]) / 10,           # 0.1A,     Output Current
            "Inv_Curr": float(row.registers[35]) / 10,          # 0.1A,     Inv Current
            "AC_InWattH": float(row.registers[36]) / 10,        # 0.1W,     AC Input watt (high)
            "AC_InWattL": float(row.registers[37]) / 10,        # 0.1W,     AC Input watt (low)
            "AC_InVAH": float(row.registers[38]) / 10,          # 0.1A,     AC Input VA (high)
            "AC_InVAL": float(row.registers[39]) / 10,          # 0.1A,     AC Input VA (low)
            "Faultbit": float(row.registers[40]),               # &*1
            "Warnbit": float(row.registers[41]),                # &*1
            "Faultvalue": float(row.registers[42]),             # fault value
            "Warnvalue": float(row.registers[43]),              # warn value
            "DTC": float(row.registers[44]),                    #
            "CheckStep": float(row.registers[45]),              #
            "ProductionLM": float(row.registers[46]),           #
            "ConstPOKF": float(row.registers[47]),                # Constant power ok flag (0 no, 1 OK)
            "Epv1_todayH": float(row.registers[48]) / 10,       # 0.1kWh,   Energy today H,     Today generate energy (high)
            "Epv1_todayL": float(row.registers[49]) / 10,       # 0.1kWh,   Energy today l,     Today generate energy (low)
            "Epv1_totalH": float(row.registers[50]) / 10,       # 0.1kWh,   Energy total H,     generate energy total (high)
            "Epv1_totalL": float(row.registers[51]) / 10,       # 0.1kWh,   Energy total l,     generate energy total (low)
            "Epv2_todayH": float(row.registers[52]) / 10,       # 0.1kWh,   Energy today H,     Today generate energy (high)
            "Epv2_todayL": float(row.registers[53]) / 10,       # 0.1kWh,   Energy today l,     Today generate energy (low)
            "Epv2_totalH": float(row.registers[54]) / 10,       # 0.1kWh,   Energy total H,     generate energy total (high)
            "Epv2_totalL": float(row.registers[55]) / 10,       # 0.1kWh,   Energy total l,     generate energy total (low)
            "Eac_chrtodayH": float(row.registers[56]) / 10,     # 0.1kWh,   AC charge Energy Today (high)
            "Eac_chrtodayL": float(row.registers[57]) / 10,     # 0.1kWh,   AC charge Energy Todat (low)
            "Eac_chrtotalH": float(row.registers[58]) / 10,     # 0.1kWh,   AC charge Energy Total (high)
            "Eac_chrtotalL": float(row.registers[59]) / 10,     # 0.1kWh,   AC charge Energy Total (low)
            "Ebat_chrtodayH": float(row.registers[60]) / 10,    # 0.1kWh,   Bat discharge Energy Today (high)
            "Ebat_chrtodayL": float(row.registers[61]) / 10,    # 0.1kWh,   Bat discharge Energy Todat (low)
            "Ebat_chrtotalH": float(row.registers[62]) / 10,    # 0.1kWh,   Bat discharge Energy Total (high)
            "Ebat_chrtotalL": float(row.registers[63]) / 10,    # 0.1kWh,   Bat discharge Energy Total (low)
            "Eac_dischrtodayH": float(row.registers[64]) / 10,  # 0.1kWh,   AC discharge Energy Today (high)
            "Eac_dischrtodayL": float(row.registers[65]) / 10,  # 0.1kWh,   AC discharge Energy Todat (low)
            "Eac_dischrtotalH": float(row.registers[66]) / 10,  # 0.1kWh,   AC discharge Energy Total (high)
            "Eac_dischrtotalL": float(row.registers[67]) / 10,  # 0.1kWh,   AC discharge Energy Total (low)
            "Acchrcurr": float(row.registers[68]) / 10,         # 0.1A,     AC Charge Battery Current
            "AC_dischrwattH": float(row.registers[69]) / 10,    # 0.1W,     AC discharge watt (high)
            "AC_dischrwattL": float(row.registers[70]) / 10,    # 0.1W,     AC discharge watt (low)
            "AC_dischrvaH": float(row.registers[71]) / 10,      # 0.1VA     AC discharge va (high)
            "AC_dischrvaL": float(row.registers[72]) / 10,      # 0.1VA     AC discharge va (low)
            "Bat_dischrwattH": float(row.registers[73]) / 10,   # 0.1W      Bat discharge watts (high)
            "Bat_dischrwattL": float(row.registers[74]) / 10,   # 0.1W      Bat discharge watts (low)
            "Bat_dischrvaH": float(row.registers[75]) / 10,     # 0.1VA     Bat discharge va (high)
            "Bat_dischrvaL": float(row.registers[76]) / 10,     # 0.1VA     Bat discharge va (low)
            "Bat_wattH": float(row.registers[77]) / 10,         # 0.1W      Signed int positive discharge, negative battery charge power
            "Bat_wattL": float(row.registers[78]) / 10,         # 0.1W      Signed int positive discharge, negative battery charge power
            "Batovercharge": float(row.registers[80]),          # 0 no, 1 yes
            "Mpptfanspeed": float(row.registers[81]),           # 1%        Fan speed of MPPT Charger
            "Invfanspeed": float(row.registers[82]),            # 1%        Fan speed of Inverter
        }
        if gwinfodump: print(info)
        return info

# Do some shit

print("Establishing connection to Influx..", end="")
try:
  influx = InfluxDBClient(host=influxhost, port=influxport,username=influxuser,password=influxpass,database=influxdbname)
except:
  print("Failed")
  exit()
else:
  print("Done!")

print("Creating Influx Database ",influxdbname," ..", end="")
try:
    influx.create_database(influxdbname)
except:
  print("Failed")
  exit()
else:
  print("Done!")

print("Connecting to Inverter..", end="")
try:
  client = ModbusClient(method='rtu', port=inverterusbport1, baudrate=9600, stopbits=1, parity='N', bytesize=8, timeout=1)
  client.connect()
except:
  print("Failed")
else:
 print("Done!")



print("Loading inverters.. ", end="")
inverters = []
for i in range(numinverters):
  #unit is this concept in modbus of an address of the thing you are talking to on the bus
  #it should be 1 for gw1, 2 for gw2, etc..etc  be sure to set any addressable things on the bus
  #to a different unit number
  #it looks like growatt it 
  unit=i+1
  name = "Growatt"+str(unit)
  measurement=influxmeasurement+str(unit)
  print("Name ",name," unit is ",unit," measurement is ",measurement)
  growatt = Growatt(client, name, unit)
  inverters.append({
    'growatt': growatt,
    'measurement': measurement
  })
print("Done!")

while True:
    for inverter in inverters:
        growatt = inverter['growatt']
        print(growatt.name)
        try:
            now = time.time()
            info = growatt.read()

            if info is None:
                continue

            if verbose: print("CHECK4")
            points = [{
                'time': int(now),
                'measurement': inverter['measurement'],
                "fields": info
            }]
            if verbose: print("CHECK5")

            if not influx.write_points(points, time_precision='s'):
                print("Failed to write to DB!")
        except Exception as err:
            if verbose: print("ERRORHERE1")
            print(err)

        time.sleep(interval)
