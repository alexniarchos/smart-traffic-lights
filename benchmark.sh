set -x

python ./src/maxpressure.py --scenario 3x3-grid
python ./src/webster.py --scenario 3x3-grid

python ./src/maxpressure.py --scenario 4x4-grid
python ./src/webster.py --scenario 4x4-grid

python ./src/maxpressure.py --scenario arterial-road
python ./src/webster.py --scenario arterial-road

python ./src/maxpressure.py --scenario real-world
python ./src/webster.py --scenario real-world

python ./src/maxpressure.py --scenario single-intersection
python ./src/webster.py --scenario single-intersection

python ./src/maxpressure.py --scenario unbalanced-intersection
python ./src/webster.py --scenario unbalanced-intersection
