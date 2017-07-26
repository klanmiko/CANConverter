import csv
import os
import sys
from datetime import datetime
path = sys.argv[1]
os.chdir(path)
HV_Only = False
response = raw_input('Do you want to filter only messages where car is in HV State? (Y/N) ')
if response == 'Y':
    HV_Only = True
class State:
    time = 0
    throttle = 0
    brake = 0
    temp_array = [0, 0, 0, 0, 0, 0]
    state = 0
    soc = 0
    bms_status = 'No Error'
    min_volt = 0
    max_volt = 0
    pack_volt = 0
    curr_dir = 0
    curr_amp = 0
    def printHeader(self, writer):
        writer.writerow(['Timestamp', 'State', 'Throttle', 'Brake',
                         'Cell 1', 'Cell 2', 'Cell 3', 'Cell 4', 'Cell 5', 'Cell 6',
                         'SOC', 'BMS State', 'Cell Min Voltage', 'Cell Max Voltage', 'Pack Voltage',
                         'Charging', 'Current Flow'])
    def printRow(self, writer):
        part = [self.time, self.printState(self.state), self.throttle, self.brake]
        part.extend(self.temp_array)
        part.extend([self.soc, self.bms_status, self.min_volt, self.max_volt, self.pack_volt,
                     self.curr_dir, self.curr_amp])
        writer.writerow(part)
    def printState(self, state):
        if state == 0:
            return 'Startup'
        if state == 1:
            return "LV"
        if state == 2:
            return "Pre-charge"
        if state == 3:
            return "HV-Enabled"
        if state == 4:
            return 'Drive'
        if state == 5:
            return 'Fault'
class Filter:
    state = State()
    shouldWrite = False
    def read512(self, data):
        self.state.throttle = str(int(data[1] + data[2], 16) / float(0x7FFF) * 100) + '%'
    def read513(self, data):
        self.state.brake = str(int(data[1] + data[2], 16)) + '%'
    def read1574(self, data):
        self.state.state = int(data[0], 16)
    def read904(self, data):
        self.state.min_volt = str(int(data[0] + data[1], 16)) + 'mV'
        self.state.max_volt = str(int(data[2] + data[3], 16)) + 'mV'
        self.state.pack_volt = str(int(data[4] + data[5] + data[6] + data[7], 16)) + 'mV'
    def read1160(self, data):
        self.state.temp_array = map(int, data[:6])
    def read648(self, data):
        self.state.curr_dir = int(data[0], 16)
        if self.state.curr_dir == 0:
            self.state.curr_dir = 'discharging'
        else:
            self.state.curr_dir = 'charging'
        self.state.curr_amp = str(int(data[1] + data[2], 16)) + 'A'
    def read392(self, data):
        status = int(data[2] + data[3], 16)
        self.state.bms_status = ''
        self.state.soc = int(data[1], 16)
        if (status & 0x01) == 0x01:
            self.state.bms_status = 'Charge mode '
        if (status & 0x02) == 0x02:
            self.state.bms_status += 'Pack temperature limit exceeded '
        if (status & 0x04) == 0x04:
            self.state.bms_status += 'Pack temperature limit close '
        if (status & 0x08) == 0x08:
            self.state.bms_status += 'Pack temperature low limit '
        if (status & 0x10) == 0x10:
            self.state.bms_status += 'Low SOC '
        if (status & 0x20) == 0x20:
            self.state.bms_status += 'Critical Soc '
        if (status & 0x40) == 0x40:
            self.state.bms_status += 'Imbalance '
        if (status & 0x80) == 0x80:
            self.state.bms_status += 'Internal Fault (6804 comm fail) '
        if (status & 0x100) == 0x100:
            self.state.bms_status += 'Negative contactor closed '
        if (status & 0x100) == 0x100:
            self.state.bms_status += 'Positive contactor closed '
        if (status & 0x200) == 0x200:
            self.state.bms_status += 'Negative contactor closed '
        if (status & 0x400) == 0x400:
            self.state.bms_status += 'Isolation fault '
        if (status & 0x800) == 0x800:
            self.state.bms_status += 'Cell too high '
        if (status & 0x1000) == 0x1000:
            self.state.bms_status += 'Charge too high '
        if (status & 0x2000) == 0x2000:
            self.state.bms_status += 'Charge fault '
        if (status & 0x4000) == 0x4000:
            self.state.bms_status += 'Full '
        if (status & 0x8000) == 0x8000:
            self.state.bms_status += 'Precharge contactor closed '
        if self.state.bms_status == '':
            self.state.bms_status = 'No Error'
    functions = {
        1574: read1574,
        513: read513,
        512: read512,
        392: read392,
        904: read904,
        1160: read1160,
        648: read648
    }
    def readLine(self, row):
        can = int(row[0], 16)
        self.state.time = int(row[1])
        data = row[2:]
        try:
            self.functions[can](self, data)
            if HV_Only:
                if self.state.state < 3:
                    self.shouldWrite = False
                else:
                    self.shouldWrite = True
        except KeyError:
            pass
    def writeLine(self, writer):
        if self.shouldWrite:
            self.state.printRow(writer)
            self.shouldWrite = False
for f in os.listdir(path):
    with open(f, 'r') as infile:
        filter = Filter()
        reader = csv.reader(infile)
        print 'Reading: ' + f
        with open("Filtered/"+f, 'w') as output:
            writer = csv.writer(output)
            filter.state.printHeader(writer)
            for row in reader:
                filter.readLine(row)
                filter.writeLine(writer)
        print 'Written: ' + f