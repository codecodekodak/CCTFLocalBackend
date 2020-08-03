#!/usr/bin/env python3

from scapy.all import *
from db import DB
import sys

import string

from beautyLogger import BeautyLogger
log = BeautyLogger("importer")

### TCP
filename = ""
flows_to_import = []  # flow which will be imported into the db
done = 0
start_time = {}
inx = 0

data_flow = {}  # data inside flows identified by tcp addr
ts = {}  # timestamp of flows identified by tcp addr


### UDP
udp_to_import = []
done_UDP = 0

### ICMP
icmp_to_import = []
done_ICMP = 0



if len(sys.argv) == 2:
    filename = sys.argv[1]
    if "./" in filename:
        filename = filename[2:]
    log.printInfo("Importing pcaps from " + filename)
else:
    log.printError("pcap file required")
    exit()

def setFlowToBeImported(key):
    global done
    done += 1
    if done % 10 == 0:
        log.printInfo(str(done) + " flows elaborated")

    if len(data_flow[key]) == 0:  # if flow is empty
        log.printWarn("Got an empty flow")
        return

    flow = {"inx": inx,
            "filename": filename,
            "src_ip": src,
            "src_port": sport,
            "dst_ip": dest,
            "dst_port": dport,
            "time": start_time[key],
            "duration": (timestamp - start_time[key]),
            "flow": data_flow[key]
            }

    flows_to_import.append(flow)
    del data_flow[key]

def setUDPToBeImported(p):
    global done_UDP
    done_UDP += 1
    if done_UDP % 10 == 0:
        log.printInfo(str(done_UDP) + " UDP packets elaborated")
    udp_to_import.append(p)

def setICMPToBeImported(p):
    global done_ICMP
    done_ICMP += 1
    if done_ICMP % 10 == 0:
        log.printInfo(str(done_ICMP) + " ICMP packets elaborated")
    icmp_to_import.append(p)




packets = rdpcap(filename)
log.printInfo("Found " + str(len(packets)) + " packets")

# let's iterate through every packet
for packet in packets:
    if packet.haslayer(TCP):
        flags = packet[TCP].flags
        dest = packet[IP].dst
        src = packet[IP].src
        dport = packet[TCP].dport
        sport = packet[TCP].sport
        timestamp = packet.time * 1000 #Convert to millisec timestamp
        key = (src, dest, sport, dport)

        if flags.S:  # start connection init resources
            if (dest, src, dport, sport) in data_flow.keys():  # more SYNC packets, take only the first
                continue
            data_flow[key] = []
            start_time[key] = timestamp

        else:
            if key in data_flow.keys():  # client is sending to the server
                name = "c"
            else:
                name = "s"
                key = (dest, src, dport, sport)

            if packet.haslayer(Raw):  # contains data
                data = packet[Raw].load
                printable_data = ''.join([chr(i) if chr(i) in string.printable else '\\x{:02x}'.format(i) for i in data])  # convert data to printable data
                #hex_data = data.hex()

                if key in data_flow.keys():
                    last_flow = (data_flow[key] or [None])[-1]
                else:
                    last_flow = None
                    data_flow[key] = []
                    start_time[key] = timestamp

                # if this is from server, and last one received was from server then just concatenate data
                if last_flow and last_flow["from"] == name:
                    data_flow[key][-1]["data"] += printable_data
                    #data_flow[key][-1]["hex"] += hex_data
                else:  # add a new data flow
                    data_flow[key].append(
                        {"from": name,
                         "data": printable_data,
                         "time": timestamp,
                         "flags": flags
                         }
                    )

            elif (flags.F and flags.A) or flags.R:  # end of the connection
                if key not in data_flow:  # already elaborated previously
                    continue
                setFlowToBeImported(key)

    elif packet.haslayer(UDP):
        dest = packet[IP].dst
        src = packet[IP].src
        dport = packet[UDP].dport
        sport = packet[UDP].sport
        timestamp = packet.time * 1000 #Convert to millisec timestamp
        data="empty"

        if packet.haslayer(Raw):  # contains data
            data = packet[Raw].load
            data = ''.join([chr(i) if chr(i) in string.printable else '\\x{:02x}'.format(i) for i in data])  # convert data to printable data
            #hex_data = data.hex()
        udpPacket = {
            "filename": filename,
            "src_ip": src,
            "src_port": sport,
            "dst_ip": dest,
            "dst_port": dport,
            "time": timestamp,
            "data": data
        }

        setUDPToBeImported(udpPacket)


    elif packet.haslayer(ICMP):
        code = packet[ICMP].code
        dest = packet[IP].dst
        src = packet[IP].src
        gw = packet[ICMP].gw
        addr_mask = packet[ICMP].addr_mask
        timestamp = packet.time * 1000 #Convert to millisec timestamp
        
        icmpPacket = {
            "filename": filename,
            "src_ip": src,
            "dst_ip": dest,
            "time": timestamp,
            "code": code,
            "gw": gw,
            "addr_mask": addr_mask
        }

        setICMPToBeImported(icmpPacket)





#if there are some flows not closed just import them
last_flows = list(data_flow.keys())
for key in last_flows:
    setFlowToBeImported(key)

db = DB()

db.delete_all_filenames(filename)
db.delete_all_pcaps(filename)

log.printInfo("Importing " + str(len(flows_to_import)) +
              " flows into mongodb!")
# when scapy finishes flowns to import has all the data ready to be inserted into the db
db.insertFlows(filename, flows_to_import)
db.insertUDP(filename, udp_to_import)
db.insertICMP(filename, icmp_to_import)
db.setFileImported(filename)