#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import sys
import pprint
from beautyLogger import BeautyLogger
log = BeautyLogger("MongoConnector")

mongo_server = 'mongodb://127.0.0.1:27017/'


class DB:
    def __init__(self):
        try:
            self.client = MongoClient(
                mongo_server, serverSelectionTimeoutMS=200)
            self.client.server_info() # to test the connection
            self.db = self.client.pcap # create/choose database
            self.pcap_coll = self.db.pcap # create pcap collection
            self.file_coll = self.db.filesImported # create filesImported collection
        except ServerSelectionTimeoutError as err:
            log.printError("MongoDB server not active on %s\n%s" % (mongo_server,err))
            sys.exit(1)
        log.printGoodNews("Successfully connected to the MongoDB instance")


    def isFileAlreadyImported(self, file_name):
        return self.file_coll.find({"file_name": file_name}).count() != 0

    def setFileImported(self, file_name):
        return self.file_coll.insert({"file_name": file_name})

    def insertFlows(self, filename, flows):
        if self.isFileAlreadyImported(filename):
            log.printWarn(filename + " pcap already present! Not importing it!")
            return
        result = self.pcap_coll.insert_many(flows)
        log.printInfo("Result inserting: " + str(result))
        # TODO - create index for each field in the table if not present before
        # col.create_index([("time", ASCENDING)])
        # col.create_index([('flow.data', 'text')])
        return result

    def delete_all_pcaps(self, filename):
        return self.pcap_coll.remove({})

    def delete_all_filenames(self, filename):
        return self.file_coll.remove({})



"""
    def getFlowList(self, filters):
        #log.printInfo("getFlowList filters param: " + pprint.pformat(filters))
        limit = 10 # TODO - fix query results found number adding it as part of the response
        sort = -1 # newer first
        f = {}
        if "flow.data" in filters:
            log.printInfo("Compiling " + filters["flow.data"] + " as regex")
            f["flow.data"] = re.compile(filters["flow.data"], re.IGNORECASE)
        if "service" in filters:
            for a in services:
                if(a["name"] == filters["service"]):
                    f["dst_port"] = a["port"]
            if "dst_port" not in f:
                log.printWarn("Unknown port for service: " + filters["service"])
        if "older" in filters:
            if(filters["older"] == True):
                sort = 1

        if "attacks" in filters:
            if filters["attacks"] == "only":
                log.printInfo("Attacks only")
                if "flow.data" in f:
                    #f["flow.data"] = {f["flow.data"], re.compile(regex_flag)} TODO - FIX THIS, matching 2 regex on the same field
                    f["flow.data"] = f["flow.data"]
                else:
                    f["flow.data"] = re.compile(regex_flag)
            elif filters["attacks"] == "exclude":
                log.printInfo("Exclude attacks")
                if "flow.data" in f:
                    #f["flow.data"] = {f["flow.data"], {"$not":re.compile(regex_flag)}} TODO - FIX THIS, matching 2 regex on the same field
                    f["flow.data"] = f["flow.data"]
                else:
                    f["flow.data"] = {"$not": re.compile(regex_flag)}
        #if "dst_ip" in filters:
        #    f["dst_ip"] = filters["dst_ip"]
        #if "dst_port" in filters:
        #    f["dst_port"] = int(filters["dst_port"])
        '''if "from_time" in filters and "to_time" in filters:
            f["time"] = {"$gte": int(filters["from_time"]),
                         "$lt": int(filters["to_time"])}
        if "starred" in filters:
            f["starred"] =  filters["starred"]'''
        if "limit" in filters:
            limit = filters["limit"]

        log.printInfo("query: " + pprint.pformat(f))

        if "near" in filters and len(filters['near'])==24:
            nearFilterBefore = {}
            nearFilterAfter = {}
            #print("FILTRO NEAR: " + filters["near"])
            #print(self.pcap_coll.find_one({"_id":ObjectId(filters["near"])}, {"flow": 0})['time'])
            referenceFlowTime = int(self.pcap_coll.find_one({"_id":ObjectId(filters["near"])}, {"flow": 0})['time'])
            referenceFlowDestPort = int(self.pcap_coll.find_one({"_id":ObjectId(filters["near"])}, {"flow": 0})["dst_port"])
            #log.printInfo("Reference time for near packets: " + str(referenceFlowTime))
            #log.printInfo("Reference port for near packets: " + str(referenceFlowDestPort))

            nearFilterBefore["dst_port"] = referenceFlowDestPort
            nearFilterAfter["dst_port"] = referenceFlowDestPort

            nearFilterBefore["time"] = {"$lt": referenceFlowTime}
            nearFilterAfter["time"] = {"$gt": referenceFlowTime}

            result = list(self.pcap_coll.find(nearFilterBefore, {"flow": 0}).sort("time", -1).limit(5))[::-1] + list(self.pcap_coll.find(nearFilterAfter, {"flow": 0}).sort("time", 1).limit(6))
            found = False
            for a in result:
                if(str(a["_id"]) == filters["near"]):
                    log.printInfo("Found duplicate while searching for near flows, not insering it")
                    found = True

            if not found:
                result = result[0:5] + list(self.pcap_coll.find({"_id":ObjectId(filters["near"])}, {"flow": 0}).limit(1)) + result[5:]
            return result

        return self.pcap_coll.find(f, {"flow": 0}).sort("time", sort).limit(limit)

    def getStarred(self):
        sort = -1 # newer first
        f = {}
        f["starred"] = 1
        return self.pcap_coll.find(f, {"flow": 0}).sort("time", sort)

    def getFlowDetail(self, id):
        flow = self.pcap_coll.find_one({"_id": ObjectId(id)})

        #colourFormat = '\033[{0}m'
        colourFormat = '\033[48;5;{}m'
        #colourStr = colourFormat.format(32)
        colourStr = colourFormat.format(5)
        #resetStr = colourFormat.format(0)
        resetStr = '\033[0m'
        
        # highlight flag here
        for i in range(0, len(flow["flow"])):
            s = flow["flow"][i]["data"]
            lastMatch = 0
            formattedText = ''
            found = False
            for match in re.finditer(regex_flag, s):
                found = True
                start, end = match.span()
                formattedText += s[lastMatch: start]
                formattedText += colourStr
                formattedText += s[start: end]
                formattedText += resetStr
                lastMatch = end
            formattedText += s[lastMatch:]
            flow["flow"][i]["data"] = formattedText
            if found is True:
                flow["contains_flag"] = True
        
        return flow

    def hasFlag(self, id):
        flow = self.pcap_coll.find_one({"_id": ObjectId(id)})
        # find flag here
        for i in range(0, len(flow["flow"])):
            s = flow["flow"][i]["data"]
            found = False
            if re.search(regex_flag, s):
                return {"contains_flag":True}
        return {"contains_flag":False}


    def setStar(self, flow_id, star):
        self.pcap_coll.find_one_and_update({"_id": ObjectId(flow_id)}, {"$set": {"starred":  1 if star == '1' else 0}})
"""