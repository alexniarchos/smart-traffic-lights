# smart-traffic-lights
This project aims to improve the traffic flow of various real-world  simulated scenarios
Smart traffic lights using SUMO simulator


## Install Python
```
sudo apt install python3 python3.10-venv python3-pip
python3 -m venv ./env
```

## Install SUMO
```
pip install -r requirements.txt
```

## Environment variables

Setup `SUMO_HOME` on your shell configuration

```
export SUMO_HOME="path-to-sumo-folder"
```

## Activate virtual environment
```
source ./bin/activate 
```

## Run a simulation
```
python3 ./src/starter.py
```
