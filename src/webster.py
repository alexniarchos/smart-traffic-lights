import os
import traci
import math
from TrafficLight import TrafficLight
from TrafficLightLink import TrafficLightLink
from dotenv import load_dotenv


trafficLights = []


def setupSumo():
  load_dotenv()
  sumoBinary = os.getenv("SUMO_BINARY")
  sumoCmd = [sumoBinary, "-c", os.getenv("SUMO_CONFIG")]
  traci.start(sumoCmd)


def resolveLinkIds(state, links):
  relatedLinks = []
  for index, val in enumerate(state):
    if state[index] == 'G':
      relatedLinks.append(links[index][0][2])
  return relatedLinks


def calculateTimeLost(phases):
  totalTimeLost = 0
  for phase in phases:
    if 'G' not in phase.state:
      totalTimeLost += phase.duration * 0.75
  return math.ceil(totalTimeLost) + len(phases)


def setupTrafficLights():
  idList = traci.trafficlight.getIDList()
  for id in idList:
    links = traci.trafficlight.getControlledLinks(id)
    trafficLight = TrafficLight(id, [], [])
    for link in links:
      trafficLight.links.append(TrafficLightLink(link[0][2], link[0][0], link[0][1]))
    currProgram = int(traci.trafficlight.getProgram(id))
    for phase in traci.trafficlight.getAllProgramLogics(id)[currProgram].phases:
      trafficLight.linksByPhaseId.append(resolveLinkIds(phase.state, links))
    trafficLights.append(trafficLight)


def calculateNextLane(route, currentLane):
  currentRoad = currentLane.split('_')[0]
  for index, road in enumerate(route):
    if road == currentRoad:
      if (index == len(route) - 1):
        return -1
      else:
        return route[index + 1]


def calculatePreviousLane(route, currentLane):
  currentRoad = currentLane.split('_')[0]
  for index, road in enumerate(route):
    if road == currentRoad:
      if (index == 0):
        return -1
      else:
        return route[index - 1]


def calculateVehicles(step):
  for trafficLight in trafficLights:
    for link in trafficLight.links:
      link.numberOfIncomingCars = 0
      link.numberOfOutgoingCars = 0
  for vehicle in traci.vehicle.getIDList():
    route = traci.vehicle.getRoute(vehicle)
    currentLane = traci.vehicle.getLaneID(vehicle)
    previousLane = calculatePreviousLane(route, currentLane)
    nextLane = calculateNextLane(route, currentLane)
    for trafficLight in trafficLights:
      for link in trafficLight.links:
        if link.to == currentLane and link.of.split('_')[0] == previousLane:
          link.numberOfOutgoingCars += 1
          if vehicle not in trafficLight.totalOutcomingVehicles:
            trafficLight.totalOutcomingVehicles[vehicle] = step
        if link.of == currentLane and link.to.split('_')[0] == nextLane:
          link.numberOfIncomingCars += 1
          if vehicle not in trafficLight.totalIncomingVehicles:
            trafficLight.totalIncomingVehicles[vehicle] = step


def setupWebster():
  idList = traci.trafficlight.getIDList()
  for id in idList:
    programLogic = traci.trafficlight.getAllProgramLogics(id)[0]
    timeLost = calculateTimeLost(traci.trafficlight.getAllProgramLogics(id)[0].phases)
    totalTime = math.ceil((1.5 * timeLost + 5) / 0.3)
    numberOfLinks = len(traci.trafficlight.getControlledLinks(id))
    for phase in programLogic.phases:
      timeForPhase = math.ceil((phase.state.count('G') * totalTime)/numberOfLinks)
      if 'G' in phase.state:
        phase.duration = timeForPhase
        phase.minDur = timeForPhase
        phase.maxDur = timeForPhase
    traci.trafficlight.setProgramLogic(id, programLogic)

step = 0
setupSumo()
setupTrafficLights()
setupWebster()
while step < 1000:
  calculateVehicles(step)
  traci.simulationStep()
  step += 1

allIntersectionTime = 0
allIntersectionVehicles = 0
for trafficLight in trafficLights:
  totalTime = 0
  for vehicle in trafficLight.totalOutcomingVehicles:
    if vehicle in trafficLight.totalIncomingVehicles:
      totalTime += trafficLight.totalOutcomingVehicles[vehicle] - trafficLight.totalIncomingVehicles[vehicle]
  print("TrafficLight:", trafficLight.id)
  print("Average Time:", totalTime / len(trafficLight.totalOutcomingVehicles))
  print("Total Outcoming vehicles:", len(trafficLight.totalOutcomingVehicles))
  print("Total Incoming vehicles:", len(trafficLight.totalIncomingVehicles))
  allIntersectionVehicles += len(trafficLight.totalOutcomingVehicles)
  allIntersectionTime += totalTime

print("All intersection time:", allIntersectionTime / allIntersectionVehicles)
traci.close()
