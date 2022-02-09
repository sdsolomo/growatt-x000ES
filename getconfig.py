#!/usr/bin/env python3

#Error Codes?
#def read_config(self): 0-72 store in db

import time
import datetime
import os
import sys
from pymodbus.exceptions import ModbusIOException
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from influxdb import InfluxDBClient

influxhost = "127.0.0.1"
influxport = "8086"
influxdbname = "growattconfig"
influxuser = "None"
influxpass = "None"
influxmeasurement = "config"

interval = 3600

numinverters = 1
inverterusbport1 = "/dev/ttyUSB0"
#not sure yet if the inverters will allow me to poll them over a single usb connection or not
inverterusbport2 = "/dev/ttyUSB1"
inverterusbport3 = "/dev/ttyUSB2"

verbose = 0

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
            if verbose: print("CHECK1",row)
            raise row
        self.modbusVersion = row.registers[0]

    def read(self):
        row = self.client.read_holding_registers(0, 81, unit=self.unit)
        if verbose: print("CHECK2")
        info = {                                                        # ==================================================================
            "StatusCode": row.registers[0],                             # 0000 off,outputon 0001 on,outen 0100 off/disa 0101 on,disa
            "OutputConfig": row.registers[1],                           # 0 bat first, 1 pv first, 2 uti first
            "ChargeConfig": row.registers[2],                           # 0 PV first, 1 pv&uti, 2 PV only
            "UtiOutStart": row.registers[3],                            # 0-23 (Hours)
            "UtiOutEnd": row.registers[4],                              # 0-23 (Hours)
            "UtiChargeStart": row.registers[5],                         # 0-23 (Hours)
            "UtiChargeEnd": row.registers[6],                           # 0-23 (Hours)
            "PVmodel": row.registers[7],                                # 0 independent, 1 parallel
            "ACInModel": row.registers[8],                              # 0 APL,90-280vac UPS 170-280vac
            "FwVersionH": row.registers[9],                             #
            "FwVersionM": row.registers[10],                            #
            "FwVersionH": row.registers[11],                            #
            "FwVersion2H": row.registers[12],                             #
            "FwVersion2M": row.registers[13],                            #
            "FwVersion2H": row.registers[14],                            #
            "OutputVoltType": row.registers[18],                           #0:208, 1:230, 2:240
            "OutputFreqType": row.registers[19],                           #0:50hz 1:60hz
            "OverLoadRestart": row.registers[20],                           #0yes, 1 no, 2switch to uti
            "OverTempRestart": row.registers[21],                           #0yes, 1 no
            "BuzzerEN": row.registers[22],                           #0 no,1 yes,
            "Serno5": row.registers[23],                           #
            "Serno4": row.registers[24],                           #
            "Serno3": row.registers[25],                           #
            "Serno2": row.registers[26],                           #
            "Serno1": row.registers[27],                           #
            "MoudleH": row.registers[28],                           #
            "MoudleL": row.registers[29],                           #P0 lead, 1 lithium, 2 customlead  User 0 no, 1growatt, 2cps, 3haiti M 3kw 5kw, Saging 0 norm/1aging
            "ComAddress": row.registers[30],                           #1-254
            "FlashStart": row.registers[31],                           #0001-own, 0100 control board
            "MaxChargeCurr": row.registers[34],                           #10-130
            "BulkChargeVolt": float(row.registers[35]) / 10,            #.1v 500-580
            "FloatChargeVolt": float(row.registers[36]) / 10,            #.1v 500-560
            "BatLowtoUtiVolt": float(row.registers[37]) / 10,            #.1v 444-514
            "FloatChargeCurr": float(row.registers[38]) / 10,            #.1a 0-80
            "BatteryType": row.registers[39],                           #0 lead acid, 1 lithium, 2 customLead
            "Aging Mode": row.registers[40],                           #0 normal, 1 aging mode
            "DTC": row.registers[43],                           #&*6
            "SysYear": row.registers[45],                           #
            "SysMonth": row.registers[46],                           #
            "SysDay": row.registers[47],                           #
            "SysHour": row.registers[48],                           #
            "SysMin": row.registers[49],                           #
            "SysSec": row.registers[50],                           #
            "FWBuild4": row.registers[67],                           #
            "FWBuild3": row.registers[68],                           #
            "FWBuild2": row.registers[69],                           #
            "FWBuild1": row.registers[70],                           #
            "SysWeekly": row.registers[72],                           #0-6
            "RateWattH": float(row.registers[76]) / 10,               # 0.1w
            "RateWattL": float(row.registers[77]) / 10,               # 0.1w
            "RateVAH": float(row.registers[78]) / 10,               # 0.1w
            "RateVAL": float(row.registers[79]) / 10,               # 0.1w
            "Factory": row.registers[80]                           #ODM Info Code
        }
        print(info)
        return info


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
