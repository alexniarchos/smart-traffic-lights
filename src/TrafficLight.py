from typing import List
from TrafficLightLink import TrafficLightLink


class TrafficLight:
  id = ""
  links: List[TrafficLightLink] = []
  linksByPhaseId = []
  pressureByPhaseId = []
  currentPhaseMinEnd = 0
  inBetweenPhase = False
  inBetweenPhaseEnd = 0
  totalIncomingVehicles = {}
  totalOutcomingVehicles = {}

  def __init__(self, id, links, linksByPhaseId):
    self.id = id
    self.links = links
    self.linksByPhaseId = linksByPhaseId
