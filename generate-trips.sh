#!/bin/bash

scenario=$1

python ./env/lib/python3.10/site-packages/sumo/tools/randomTrips.py \
-n "./src/configs/comparative-study/$scenario/net.xml" \
-o "./src/configs/comparative-study/$scenario/trips.xml" \
-p 2 -e 5000 --fringe-factor 100000

duarouter -c ./src/configs/comparative-study/$scenario/index.sumocfg \
-t ./src/configs/comparative-study/$scenario/trips.xml \
-o ./src/configs/comparative-study/$scenario/rou.xml \
--ignore-errors --remove-loops
