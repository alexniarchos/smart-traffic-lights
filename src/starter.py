import os
import traci
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


def calculatePhasePressure():
  for trafficLight in trafficLights:
    trafficLight.pressureByPhaseId = []
    for index, links in enumerate(trafficLight.linksByPhaseId):
      totalIncoming = 0
      totalOutgoing = 0
      for link in links:
        for x in trafficLight.links:
          if x.linkId == link:
            totalIncoming += x.numberOfIncomingCars
            totalOutgoing += x.numberOfOutgoingCars
      trafficLight.pressureByPhaseId.append(totalIncoming - totalOutgoing)


def setNextPhase(step):
  for trafficLight in trafficLights:
    if step >= trafficLight.currentPhaseMinEnd:
      maxPressureIndex = trafficLight.pressureByPhaseId.index(max(trafficLight.pressureByPhaseId))
      currentPhase = traci.trafficlight.getPhase(trafficLight.id)
      if currentPhase != maxPressureIndex:
        if trafficLight.inBetweenPhase == False and traci.trafficlight.getPhase(trafficLight.id) % 2 == 0:
          trafficLight.inBetweenPhaseEnd = step + traci.trafficlight.getAllProgramLogics(trafficLight.id)[0].phases[currentPhase + 1].minDur
          trafficLight.inBetweenPhase = True
          traci.trafficlight.setPhase(trafficLight.id, currentPhase + 1)
        if trafficLight.inBetweenPhase == True and step >= trafficLight.inBetweenPhaseEnd:
          traci.trafficlight.setPhase(trafficLight.id, maxPressureIndex)
          trafficLight.currentPhaseMinEnd = step + traci.trafficlight.getAllProgramLogics(trafficLight.id)[0].phases[maxPressureIndex].minDur
          trafficLight.inBetweenPhase = False
      else:
        traci.trafficlight.setPhase(trafficLight.id, currentPhase)

step = 0
setupSumo()
setupTrafficLights()
while step < 1000:
  calculateVehicles(step)
  calculatePhasePressure()
  setNextPhase(step)
  traci.simulationStep()
  step += 1


totalTime = 0
for trafficLight in trafficLights:
  for vehicle in trafficLight.totalOutcomingVehicles:
    totalTime += trafficLight.totalOutcomingVehicles[vehicle] - trafficLights[0].totalIncomingVehicles[vehicle]
  print("TrafficLight:", trafficLight.id)
  print("Average Time:", totalTime/len(trafficLight.totalOutcomingVehicles))
  print("Total Outcoming vehicles:", len(trafficLight.totalOutcomingVehicles))
  print("Total Incoming vehicles:", len(trafficLight.totalIncomingVehicles))
traci.close()
