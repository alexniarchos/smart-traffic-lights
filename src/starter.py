import os, sys, subprocess

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
    from sumolib import checkBinary
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci
import numpy as np

sumoBinary = "/usr/bin/sumo-gui"
sumoCmd = [sumoBinary, "-c", "./configs/2022-02-20-15-01-25/osm.sumocfg"]

traci.start(sumoCmd)
step = 0
print(traci.trafficlight.getIDList())
while step < 1000:
  print(step)
  traci.simulationStep()
  traci.trafficlight.setRedYellowGreenState("cluster_1370816569_1372623099_1372623728_1372623894_2007178257", "GrGr")
  step += 1

traci.close()
