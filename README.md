# Growatt-X000ES Monitor
## _Simple statistics and configuration gathering scripts_


These scripts will allow you to easily gather statistics and configuration from your Growatt-5000ES or Growatt-3000ES inverter(s) using a raspberry-pi and a usb cable.  There is no need for RS485/RS232 dongles, just use the pi and the included USB cable from the inverter.

These scripts were tested using a raspberry-pi 2b running raspberrypi 5.10.92-v7+ #1514

![picture of dashboard](https://github.com/sdsolomo/growatt-x000ES/blob/main/README.png)


Installation instructions (assuming you have a working pi w/ 5.10.92-v7+ or newer w/ internet access)

First we install 4 software packages on the pi.  "Screen" allows you to run a script while you aren't logged in, python-pip will help us to install a python(programming language) module, influxdb and influxdb-client will allow us to store the data we collect. 

Open an SSH session to your pi and then:

```
sudo apt-get install screen python3-pip influxdb influxdb-client
```

I had trouble with influxdb not listening on the right interface, so now we need to make a configuration change influxdb.

Use your favorite editor to edit the config file.
```
sudo vi /etc/influxdb/influxdb.conf
```
scroll down to 
"section [http]"
and change 
```
#bind-address = ":8086"
```
to

```    
bind-address = "127.0.0.1:8086"
```
then restart influxdb
```
sudo /bin/systemctl restart influxdb
```

Now we install grafana to display the data
#go here for the latest directions.. https://grafana.com/tutorials/install-grafana-on-raspberry-pi/
#or for you lazy sob's like me just do this
```
sudo wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install -y grafana
sudo /bin/systemctl enable grafana-server
sudo /bin/systemctl start grafana-server
```

#Configure Grafana
Point your browser to http://<raspberrypiIPaddress>:3000  like http://192.168.1.1:3000
Login using username:admin and password:admin  (change the MF password)
Click on the settings gear on the left side
Click on datasources
Select "influxdb"
Scroll down to the section
"http: "
Change the URL: to  
```http://127.0.0.1:8086```
Finally, scroll down toward the bottom and name the database "growatt"
Click "Save and Test"

Almost done... Lets head back over to the ssh session to the pi 
(these can take a while.. be patient)
```
sudo pip install pymodbus
sudo pip install influxdb
```
# Test it..

Within the ssh session type
```
screen -S getconfig
```
and then
```
python3 getconfig.py
```
You should get something like this:
```
pi@raspberrypi:~ $ python3 getconfig.py 
Establishing connection to Influx..Done!
Creating Influx Database  growattconfig  ..Done!
Connecting to Inverter..Done!
Loading inverters.. Name  Growatt1  unit is  1  measurement is  config1
Done!
Growatt1
{'StatusCode': 0, 'OutputConfig': 0, 'ChargeConfig': 2, 'UtiOutStart': 0, 'UtiOutEnd': 0, 'UtiChargeStart': 0, 'UtiChargeEnd': 0, 'PVmodel': 0, 'ACInModel': 1, 'FwVersionH': 12341, 'FwVersionM': 12334, 'FwVersion2H': 12341, 'FwVersion2M': 12590, 'OutputVoltType': 2, 'OutputFreqType': 1, 'OverLoadRestart': 0, 'OverTempRestart': 1, 'BuzzerEN': 1, 'Serno5': 22866, 'Serno4': 17719, 'Serno3': 16968, 'Serno2': 14128, 'Serno1': 14392, 'MoudleH': 0, 'MoudleL': 0, 'ComAddress': 1, 'FlashStart': 256, 'MaxChargeCurr': 70, 'BulkChargeVolt': 56.4, 'FloatChargeVolt': 54.0, 'BatLowtoUtiVolt': 47.2, 'FloatChargeCurr': 3.0, 'BatteryType': 4, 'Aging Mode': 0, 'DTC': 20105, 'SysYear': 2022, 'SysMonth': 2, 'SysDay': 9, 'SysHour': 8, 'SysMin': 20, 'SysSec': 49, 'FWBuild4': 0, 'FWBuild3': 0, 'FWBuild2': 0, 'FWBuild1': 0, 'SysWeekly': 0, 'RateWattH': 0.0, 'RateWattL': 5000.0, 'RateVAH': 0.0, 'RateVAL': 5000.0, 'Factory': 5603}
```

If you get an error, wait a minute and try again.  I noticed the first time I try to connect to the inverter after attaching the usb cable, the inverter doesn't respond.  

now we detach from that screen session and start a new one for our statistics gathering.  Press ctrl-a, then hit d to detatch

```ctrl-a d```

```
screen -S getstats
python3 getstatus.py
```
Which should start polling the inverter every minute and giving you data like:
```
Establishing connection to Influx..Done!
Creating Influx Database  growatt  ..Done!
Connecting to Inverter..Done!
Loading inverters.. Name  Growatt1  unit is  1  measurement is  inverter1
Done!
Growatt1
{'Module': 1, 'StatusCode': 12, 'Status': 'PV charge and discharge', 'Vpv1': 390.0, 'Vpv2': 0.0, 'Ppv1H': 0.0, 'Ppv1L': 293.0, 'Ppv2H': 0.0, 'Ppv2L': 0.0, 'Buck1Curr': 5.9, 'Buck2Curr': 0.0, 'OP_WattH': 0.0, 'OP_WattL': 27.0, 'OP_VAH': 0.0, 'OP_VAL': 242.0, 'ACChr_WattH': 0.0, 'ACChr_WattL': 0.0, 'ACChr_VAH': 0.0, 'ACChr_VAL': 0.0, 'Bat_Volt': 49.29, 'BatterySOC': 25.0, 'BusVolt': 399.8, 'GridVolt': 245.9, 'LineFreq': 59.98, 'OutputVolt': 239.9, 'OutputFreq': 60.03, 'OutputDCV': 0.0, 'InvTemp': 6.4, 'DCDCTemp': 4.1, 'LoadPercent': 0.5, 'Bat_dspp_V': 0.0, 'Bat_dspb_V': 0.0, 'TimeTotalH': 0.0, 'TimeTotalL': 0.0, 'Buck1Temp': 2.9, 'Buck2Temp': 0.0, 'OP_Curr': 1.0, 'Inv_Curr': 2.8, 'AC_InWattH': 0.0, 'AC_InWattL': 0.0, 'AC_InVAH': 0.0, 'AC_InVAL': 0.0, 'Faultbit': 0.0, 'Warnbit': 0.0, 'Faultvalue': 0.0, 'Warnvalue': 0.0, 'DTC': 20105.0, 'CheckStep': 2556.0, 'ProductionLM': 0.0, 'ConstPOKF': 0.0, 'Epv1_todayH': 0.0, 'Epv1_todayL': 0.4, 'Epv1_totalH': 0.0, 'Epv1_totalL': 187.1, 'Epv2_todayH': 0.0, 'Epv2_todayL': 0.0, 'Epv2_totalH': 0.0, 'Epv2_totalL': 0.0, 'Eac_chrtodayH': 0.0, 'Eac_chrtodayL': 0.0, 'Eac_chrtotalH': 0.0, 'Eac_chrtotalL': 6.4, 'Ebat_chrtodayH': 0.0, 'Ebat_chrtodayL': 4.3, 'Ebat_chrtotalH': 0.0, 'Ebat_chrtotalL': 110.4, 'Eac_dischrtodayH': 0.0, 'Eac_dischrtodayL': 0.0, 'Eac_dischrtotalH': 0.0, 'Eac_dischrtotalL': 54.1, 'Acchrcurr': 0.0, 'AC_dischrwattH': 0.0, 'AC_dischrwattL': 27.0, 'AC_dischrvaH': 0.0, 'AC_dischrvaL': 242.0, 'Bat_dischrwattH': 0.0, 'Bat_dischrwattL': 0.0, 'Bat_dischrvaH': 0.0, 'Bat_dischrvaL': 0.0, 'Bat_wattH': 6553.5, 'Bat_wattL': 6277.6, 'Batovercharge': 0.0, 'Mpptfanspeed': 0.0, 'Invfanspeed': 28.0}
```
# Cool.. 

Go back to your grafana browser session
Click the 4 squares icon on the left for "Dashboards"
Click "Browse"
Click the "IMPORT" button
Select the growatt-all.json
repeat those steps for "growatt-short.json"

now you have 2 dashboards to view your data from your growatt inverter(s)... Enjoy!

## License

MIT

**Free Software, Hell Yeah!**
