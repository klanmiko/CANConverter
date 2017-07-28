import csv
import os
import sys
from datetime import datetime
path = sys.argv[1]
os.chdir(path)
for f in os.listdir(path):
    with open(f, 'r') as data:
        reader = csv.reader(data)
        reader.next()
        try:
            first = reader.next()
        except StopIteration:
            continue
        print f
        start = datetime.strptime(first[0]+"000", "%m/%d/%H:%M:%S.%f")
        can = first[2]
        string = first[3]
        s = [string[i:i+2] for i in range(0, len(string), 2)]
        with open("New/"+f, 'wb') as output:
            writer = csv.writer(output)
            firstrow = [can, 0]
            firstrow.extend(s)
            writer.writerow(firstrow)
            for row in reader:
                time = datetime.strptime(row[0], "%m/%d/%H:%M:%S.%f")
                offset = time - start
                data = row[3]
                array = [data[i:i+2] for i in range(0, len(data), 2)]
                result = [row[2], offset.seconds * 1000 + offset.microseconds / 1000]
                result.extend(array)
                writer.writerow(result)
        print 'Written: ' + first[0]
