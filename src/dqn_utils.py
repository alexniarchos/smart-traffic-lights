import itertools
import os
import shutil
import math
import traci
from utils import get_incoming_vehicles

CELL_LENGTH = 10


# def get_state(incoming_lanes, tl_id):
#     # phase = traci.trafficlight.getPhase(tl_id)
#     # phase_duration = traci.trafficlight.getPhaseDuration(tl_id)

#     vehicles_per_lane = []
#     # waiting_time_per_lane = []
#     for lane in incoming_lanes[tl_id]:
#         vehicles_per_lane.append(traci.lane.getLastStepHaltingNumber(lane))
#         # waiting_time_per_lane.append(traci.lane.getWaitingTime(lane))

#     state = vehicles_per_lane

#     return state


def get_state(incoming_lanes, tl_id):
    state = []

    for lane in incoming_lanes[tl_id]:
        lane_length = traci.lane.getLength(lane)
        cells = math.floor(lane_length / CELL_LENGTH)
        lane_state = cells * [0]

        vehicles = traci.lane.getLastStepVehicleIDs(lane)

        for vehicle in vehicles:
            lane_pos = traci.vehicle.getLanePosition(vehicle)
            state_pos = min(math.floor(lane_pos / CELL_LENGTH), cells-1)
            lane_state[state_pos] += 1

        state.append(lane_state)

    return list(itertools.chain(*state))

def get_lane_queues(incoming_lanes):
    queue_length = 0
    for lane in incoming_lanes:
        queue_length += traci.lane.getLastStepHaltingNumber(lane)

    return queue_length

def get_cur_waiting_time(incoming_lanes, old_incoming_vehicles):
    cur_incoming_vehicles = get_incoming_vehicles(incoming_lanes)

    stuck_vehicles = []

    for vehicle in old_incoming_vehicles:
        if vehicle in cur_incoming_vehicles:
            stuck_vehicles.append(vehicle)

    total_waiting_time = 0
    for vehicle in stuck_vehicles:
        waiting_time = traci.vehicle.getAccumulatedWaitingTime(vehicle)
        total_waiting_time += waiting_time

    return total_waiting_time


def set_green_phase(tl_id, tl_phases, phase):
    if phase not in tl_phases[tl_id]:
        raise Exception(f"Green phase {phase} was not found in traffic light phases")
    traci.trafficlight.setRedYellowGreenState(tl_id, phase)


def set_yellow_phase(tl_id, tl_phases, cur_phase):
    yellow_phase = cur_phase.replace("G", "y").replace("g", "y")

    if yellow_phase not in tl_phases[tl_id]:
        raise Exception(
            f"Yellow phase {yellow_phase} was not found in traffic light phases"
        )

    traci.trafficlight.setRedYellowGreenState(tl_id, yellow_phase)


def get_waiting_times(incoming_lanes, vehicle_waiting_times):
    vehicle_ids = traci.vehicle.getIDList()
    for vehicle_id in vehicle_ids:
        wait_time = traci.vehicle.getAccumulatedWaitingTime(vehicle_id)
        lane = traci.vehicle.getLaneID(vehicle_id)
        if lane in incoming_lanes:
            vehicle_waiting_times[vehicle_id] = wait_time
        else:
            # vehicle has left the intersection
            if vehicle_id in vehicle_waiting_times:
                del vehicle_waiting_times[vehicle_id]
    total_waiting_time = sum(vehicle_waiting_times.values())

    return total_waiting_time


def clean_models(scenario):
    folder_path = os.path.join(os.path.dirname(__file__), f"./models/{scenario}")

    if not os.path.exists(folder_path): 
        return

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
