class TrafficLightLink:
  linkId = None
  of = None
  to = None
  numberOfIncomingCars = 0
  numberOfOutgoingCars = 0

  def __init__(self, linkId, of, to):
    self.linkId = linkId
    self.of = of
    self.to = to
