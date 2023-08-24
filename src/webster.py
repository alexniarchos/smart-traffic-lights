import traci
from dotenv import load_dotenv
from constants import GREEN_TIME, MAX_STEPS, YELLOW_TIME
from network import get_net_data
from utils import (
    get_args,
    get_phases,
    get_phase_lanes,
    get_green_phases,
    get_sumo_cmd,
    get_tl_incoming_lanes,
)

UPDATE_INTERVAL = 500
SATURATION_FLOW = 0.38

MIN_CYCLE = 60
MAX_CYCLE = 180


def update_phase_lane_counts(
    tl_phase_lanes,
    tl_phase_lane_counts,
    tl_phase_state,
    lane_vehicles,
    prev_lane_vehicles,
):
    if prev_lane_vehicles:
        incoming_vehicles = set()
        for lane in tl_phase_lanes[tl_phase_state["cur_phase"]]:
            for vehicle in lane_vehicles[lane]:
                incoming_vehicles.add(vehicle)

        for lane in tl_phase_lanes[tl_phase_state["cur_phase"]]:
            if lane in prev_lane_vehicles:
                for vehicle in prev_lane_vehicles[lane]:
                    if vehicle not in incoming_vehicles:
                        tl_phase_lane_counts[tl_phase_state["cur_phase"]][lane] += 1

    return tl_phase_lane_counts


def get_phase_duration(phase, green_phases, green_phase_durations):
    if phase in green_phases:
        return green_phase_durations[phase]
    elif "y" in phase:
        return YELLOW_TIME


def get_empty_phase_lane_counts(phase_lanes):
    phase_lane_counts = {}
    for phase in phase_lanes:
        phase_lane_counts[phase] = {}
        for lane in phase_lanes[phase]:
            phase_lane_counts[phase][lane] = 0
    return phase_lane_counts


def get_webster_green_phase_durations(
    tl_green_phases, tl_phase_lanes, tl_phase_lane_counts
):
    ##compute flow ratios for all lanes in all green phases
    ##find critical
    y_crit = []
    for green_phase in tl_green_phases:
        saturation_flows = [
            (tl_phase_lane_counts[green_phase][lane] / UPDATE_INTERVAL)
            / (SATURATION_FLOW)
            for lane in tl_phase_lanes[green_phase]
        ]
        y_crit.append(max(saturation_flows))

    # compute intersection critical lane flow ratios
    Y = sum(y_crit)
    if Y > 0.85:
        Y = 0.85
    elif Y == 0.0:
        Y = 0.01

    # limit in case too saturated
    # compute lost time
    lost_time = len(tl_green_phases) * YELLOW_TIME

    # compute cycle time
    cycle = int(((1.5 * lost_time) + 5) / (1.0 - Y))

    # constrain if necessary
    if cycle > MAX_CYCLE:
        cycle = MAX_CYCLE
    elif cycle < MIN_CYCLE:
        cycle = MIN_CYCLE

    total_green_time = cycle - lost_time

    green_phase_durations = {}
    # compute green times for each movement
    # based on total green times
    for green_phase, y in zip(tl_green_phases, y_crit):
        green_time = int((y / Y) * total_green_time)
        # constrain green phase time if necessary
        if green_time < GREEN_TIME:
            green_time = GREEN_TIME
        green_phase_durations[green_phase] = green_time

    return green_phase_durations


def main():
    load_dotenv()
    args = get_args()
    sumo_cmd = get_sumo_cmd(args)

    traci.start(sumo_cmd)

    net_data = get_net_data(args.scenario)

    tl_ids = traci.trafficlight.getIDList()
    tl_green_phases = get_green_phases(tl_ids)
    tl_phase_lanes = get_phase_lanes(net_data, tl_ids, tl_green_phases)

    tl_prev_lane_vehicles = {tl_id: None for tl_id in tl_ids}
    tl_phase_lane_counts = {
        tl_id: get_empty_phase_lane_counts(tl_phase_lanes[tl_id]) for tl_id in tl_ids
    }
    tl_phases = get_phases(tl_ids)

    tl_phase_state = {}
    for tl_id in tl_ids:
        tl_phase_state[tl_id] = {
            "cur_phase": tl_phases[tl_id][0],
            "cur_phase_index": 0,
            "phase_durations": {
                phase: YELLOW_TIME if "y" in phase else GREEN_TIME
                for phase in tl_phases[tl_id]
            },
            "phases": tl_phases[tl_id],
            "num_of_phases": len(tl_phases[tl_id]),
        }

    time_to_change_phase = {tl_id: 0 for tl_id in tl_ids}

    tl_incoming_lanes = get_tl_incoming_lanes(net_data, tl_ids)

    total_waiting_time = 0
    total_vehicles = set()

    step = 0
    while step < MAX_STEPS:
        vehicles = traci.vehicle.getIDList()
        total_vehicles.update(set(vehicles))
        # if step > 1000 and traci.vehicle.getIDCount() == 0:
        #     print("Simulation ended at:", step)
        #     break
        for tl_id in tl_ids:
            for lane in tl_incoming_lanes[tl_id]:
                total_waiting_time += traci.lane.getLastStepHaltingNumber(lane)

            lane_vehicles = {
                lane_id: traci.lane.getLastStepVehicleIDs(lane_id)
                for lane_id in tl_incoming_lanes[tl_id]
            }

            if tl_phase_state[tl_id]["cur_phase"] in tl_green_phases[tl_id]:
                tl_phase_lane_counts[tl_id] = update_phase_lane_counts(
                    tl_phase_lanes[tl_id],
                    tl_phase_lane_counts[tl_id],
                    tl_phase_state[tl_id],
                    lane_vehicles,
                    tl_prev_lane_vehicles[tl_id],
                )

            tl_prev_lane_vehicles[tl_id] = lane_vehicles

            if step % UPDATE_INTERVAL == 0:
                phase_durations = get_webster_green_phase_durations(
                    tl_green_phases[tl_id],
                    tl_phase_lanes[tl_id],
                    tl_phase_lane_counts[tl_id],
                )
                tl_phase_lane_counts[tl_id] = get_empty_phase_lane_counts(
                    tl_phase_lanes[tl_id]
                )

                for phase in phase_durations.items():
                    tl_phase_state[tl_id]["phase_durations"][phase[0]] = phase[1]

            if time_to_change_phase[tl_id] == 0:
                cur_phase_index = tl_phase_state[tl_id]["cur_phase_index"]
                cur_phase_index = (cur_phase_index + 1) % tl_phase_state[tl_id][
                    "num_of_phases"
                ]
                tl_phase_state[tl_id]["cur_phase"] = tl_phase_state[tl_id]["phases"][
                    cur_phase_index
                ]
                tl_phase_state[tl_id]["cur_phase_index"] = cur_phase_index
                time_to_change_phase[tl_id] = tl_phase_state[tl_id]["phase_durations"][
                    tl_phase_state[tl_id]["cur_phase"]
                ]
                traci.trafficlight.setRedYellowGreenState(
                    tl_id, tl_phase_state[tl_id]["cur_phase"]
                )

            else:
                time_to_change_phase[tl_id] -= 1
        traci.simulationStep()
        step += 1

    traci.close()
    print(
        f"Total waiting time: {total_waiting_time}, Total vehicles passed: {len(vehicles)}"
    )


if __name__ == "__main__":
    main()
