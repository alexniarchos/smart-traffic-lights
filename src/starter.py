import os, sys, subprocess
import traci
import numpy as np
from dotenv import load_dotenv
load_dotenv()

print(os.getenv("SUMO_BINARY"))
print(os.getenv("SUMO_CONFIG"))
sumoBinary = os.getenv("SUMO_BINARY")
sumoCmd = [sumoBinary, "-c", os.getenv("SUMO_CONFIG")]

traci.start(sumoCmd)
step = 0
while step < 1000:
  traci.simulationStep()
  idList = traci.trafficlight.getIDList()
  allLanes = traci.lane.getIDList()
  for id in idList:
    links = traci.trafficlight.getControlledLinks(id)
    lanes = traci.trafficlight.getControlledLanes(id)
    # print("phase", phase, phaseDuration, redYellowGreenState, "endPhase")
  # traci.trafficlight.setRedYellowGreenState("cluster_1370816569_1372623099_1372623728_1372623894_2007178257", "GrGr")
  vehicles = traci.vehicle.getIDList()
  vehiclesPos = []
  vehicleDestination = []
  for vehicle in vehicles:
    vehiclesPos.append([vehicle, traci.vehicle.getLaneID(vehicle)])
    vehicleDestination.append([vehicle, '{0:14b}'.format(traci.vehicle.getSignals(vehicle))])
  step += 1

traci.close()
