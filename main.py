from flask import *
import json
import requests
import time

from flask_cors import CORS
app = Flask(__name__)
CORS(app)

# VARS
lastServerUpdate = 0

#total used free available
totalRAM = "0"
freeRAM = "0"
availableRAM = "0"

#Connections
CONNs = "" # vedere se tenerlo perchè l'output può essere troppo grande

# QUEUES
import queue

queueCpuUsage1min = queue.Queue(10)
queueCpuUsage5min = queue.Queue(10)
queueCpuUsage15min = queue.Queue(10)

queueRamUsage = queue.Queue(10)

queueServerConnections = queue.Queue(40)


############ GATEWAY VARS
lastGatewayUpdate = 0

#total used free available
totalGatewayRAM = "0"
freeGatewayRAM = "0"
availableGatewayRAM = "0"

#Connections
gatewayCONNs = "" # vedere se tenerlo perchè l'output può essere troppo grande

# QUEUES

queueGatewayCpuUsage1min = queue.Queue(10)
queueGatewayCpuUsage5min = queue.Queue(10)
queueGatewayCpuUsage15min = queue.Queue(10)

queueGatewayRamUsage = queue.Queue(10)

queueGatewayConnections = queue.Queue(40)



for _ in range(10):
    queueCpuUsage1min.put(0)
    queueCpuUsage5min.put(0)
    queueCpuUsage15min.put(0)
    queueRamUsage.put(0)
    queueGatewayCpuUsage1min.put(0)
    queueGatewayCpuUsage5min.put(0)
    queueGatewayCpuUsage15min.put(0)
    queueGatewayRamUsage.put(0)

for _ in range(40):
    queueServerConnections.put(0)
    queueGatewayConnections.put(0)


def return_response(object):
    return Response(json.dumps(object), mimetype='application/json')

def queueToJSONObject(o):
    return eval(str(o.queue)[6:-1])

def getStat(host, stat):
    global lastServerUpdate, lastGatewayUpdate
    port = 3030
    if 'gateway' in host:
        port = 3031
    try:
        response = requests.get('http://localhost:' + str(port) + '/' + str(stat), timeout=20)
        if response.status_code == 200:
            if 'gateway' in host:
                lastGatewayUpdate = time.time()
            else:
                lastServerUpdate = time.time()
        response = response.json()
        return response
    except:
        return "0"

@app.route('/')
def hello_world():
    return 'Hello world!'


###### SERVER

@app.route('/getServerCpuUsage')
def returnCpuUsage():
    return return_response([queueToJSONObject(queueCpuUsage1min), queueToJSONObject(queueCpuUsage5min), queueToJSONObject(queueCpuUsage15min)])

@app.route('/getServerMemory')
def getMemory():
    return return_response([queueToJSONObject(queueRamUsage), totalRAM, freeRAM, availableRAM])

@app.route('/getServerTop5Processes')
def getTop5Processes():
    return return_response(getStat('server', 'getTop5Processes'))

@app.route('/getServerConnections')
def getConnections():
    return return_response(getStat('server', 'getConnections'))

@app.route('/getServerConnectionsCount')
def getConnectionsCount():
    return return_response(queueToJSONObject(queueServerConnections))

@app.route('/getServerApacheLogSpaceUsage')
def getApacheLogSpaceUsage():
    return return_response(getStat('server', 'getApacheLogSpaceUsage'))

@app.route('/getServerDiskSpace')
def getDiskSpace():
    return return_response([getStat('server', 'getDiskSpace')])

@app.route('/getLastServerUpdateTime')
def getLastUpdateTime():
    return return_response([round(lastServerUpdate)])

@app.route('/killServerDeterlabTracing')
def killServerDeterlabTracing():
    return return_response(getStat('server', 'killDeterlabTracing'))

@app.route('/getServerApacheStatus')
def getServerApacheStatus():
    return return_response(getStat('server', 'testWebserver'))


##### GATEWAY

@app.route('/getGatewayCpuUsage')
def getGatewayCpuUsage():
    return return_response([queueToJSONObject(queueGatewayCpuUsage1min), queueToJSONObject(queueGatewayCpuUsage5min), queueToJSONObject(queueGatewayCpuUsage15min)])

@app.route('/getGatewayMemory')
def getGatewayMemory():
    return return_response([queueToJSONObject(queueGatewayRamUsage), totalGatewayRAM, freeGatewayRAM, availableGatewayRAM])

@app.route('/getGatewayTop5Processes')
def getGatewayTop5Processes():
    return return_response(getStat('gateway', 'getTop5Processes'))

@app.route('/getGatewayConnections')
def getGatewayConnections():
    return return_response(getStat('gateway', 'getConnections'))

@app.route('/getGatewayConnectionsCount')
def getGatewayConnectionsCount():
    return return_response(queueToJSONObject(queueGatewayConnections))

@app.route('/getGatewayApacheLogSpaceUsage')
def getGatewayApacheLogSpaceUsage():
    return return_response(getStat('gateway', 'getApacheLogSpaceUsage'))

@app.route('/getGatewayDiskSpace')
def getGatewayDiskSpace():
    return return_response([getStat('gateway', 'getDiskSpace')])

@app.route('/getLastGatewayUpdateTime')
def getLastGatewayUpdateTime():
    return return_response([round(lastGatewayUpdate)])

@app.route('/killGatewayDeterlabTracing')
def killGatewayDeterlabTracing():
    return return_response(getStat('gateway', 'killDeterlabTracing'))

@app.route('/getGatewayApacheStatus')
def getGatewayApacheStatus():
    return return_response(getStat('gateway', 'testWebserver'))

@app.route('/update')
def update():
    global totalRAM, freeRAM, availableRAM, totalGatewayRAM, freeGatewayRAM, availableGatewayRAM

    cpuTimes = getStat('server', 'getCpuUsage').split(", ")
    if(len(cpuTimes) > 2):
        queueCpuUsage1min.get()
        queueCpuUsage5min.get()
        queueCpuUsage15min.get()
        queueCpuUsage1min.put(float(cpuTimes[0]))
        queueCpuUsage5min.put(float(cpuTimes[1]))
        queueCpuUsage15min.put(float(cpuTimes[2]))
    else:
        print("Not updating server CPU usages")

    cpuGatewayTimes = getStat('gateway', 'getCpuUsage').split(", ")
    if(len(cpuGatewayTimes) > 2):
        queueGatewayCpuUsage1min.get()
        queueGatewayCpuUsage5min.get()
        queueGatewayCpuUsage15min.get()
        queueGatewayCpuUsage1min.put(float(cpuGatewayTimes[0]))
        queueGatewayCpuUsage5min.put(float(cpuGatewayTimes[1]))
        queueGatewayCpuUsage15min.put(float(cpuGatewayTimes[2]))
    else:
        print("Not updating gateway CPU usages")

    time.sleep(0.5)

    RAMs = getStat('server', 'getMemory').split(" ")
    if (len(RAMs) > 2):
        queueRamUsage.get(0)
        queueRamUsage.put(RAMs[1])
        totalRAM = RAMs[0]
        freeRAM = RAMs[2]
        availableRAM = RAMs[3]
    else:
        print("Not updating server memory usages")

    gatewayRAMs = getStat('gateway', 'getMemory').split(" ")
    if (len(gatewayRAMs) > 2):
        queueGatewayRamUsage.get(0)
        queueGatewayRamUsage.put(gatewayRAMs[1])
        totalGatewayRAM = gatewayRAMs[0]
        freeGatewayRAM = gatewayRAMs[2]
        availableGatewayRAM = gatewayRAMs[3]
    else:
        print("Not updating gateway memory usages")


    time.sleep(0.5)

    serverCconnC = getStat('server', 'getConnectionsCount')
    queueServerConnections.get()
    queueServerConnections.put(int(serverCconnC))

    gatewayConnC = getStat('gateway', 'getConnectionsCount')
    queueGatewayConnections.get()
    queueGatewayConnections.put(int(gatewayConnC))

    time.sleep(0.5)
    getStat('gateway', 'killDeterlabTracing')
    getStat('server', 'killDeterlabTracing')


    return return_response("ok")

while True:
    app.run(port=8080, debug=True)
    time.sleep(2)