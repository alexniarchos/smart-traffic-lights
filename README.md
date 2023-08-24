# smart-traffic-lights
This project aims to improve the traffic flow of various real-world  simulated scenarios
Smart traffic lights using SUMO simulator


## Install Python
```
sudo apt install python3.10 python3.10-venv python3-pip
python3.10 -m venv ./env
```

## Activate virtual environment
```
source ./env/bin/activate 
```
NOTE: Auto activation of venv in VSCode
Ctrl+Shift+P -> Python: select interpreter

## Install SUMO
```
pip install -r requirements.txt
```

## Environment variables

Setup `SUMO_HOME` on your shell configuration

```
export SUMO_HOME="path-to-sumo-folder"
```

## Run a simulation
```
python3 ./src/starter.py
```

## Generate grid network

```
netgenerate -o ./src/configs/comparative-study/<scenario>/net.xml -g --grid.number 3 --no-turnarounds
```
```
python ./env/lib/python3.10/site-packages/sumo/tools/randomTrips.py -n ./src/configs/comparative-study/3x3-grid/net.xml -o ./src/configs/comparative-study/3x3-grid/trips.xml -p 2 -e 5000 --fringe-factor 100000
```
```
duarouter -c ./src/configs/comparative-study/<scenario>/index.sumocfg -t ./src/configs/comparative-study/3x3-grid/trips.xml -o ./src/configs/comparative-study/3x3-grid/rou.xml --ignore-errors --remove-loops
```
