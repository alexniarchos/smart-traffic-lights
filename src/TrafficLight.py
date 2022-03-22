class TrafficLight:

  def __init__(self, id, links, linksByPhaseId):
    self.id = id
    self.links = links
    self.linksByPhaseId = linksByPhaseId
    self.pressureByPhaseId = []
    self.currentPhaseMinEnd = 0
    self.inBetweenPhase = False
    self.inBetweenPhaseEnd = 0
    self.totalIncomingVehicles = {}
    self.totalOutcomingVehicles = {}
