import traci
from dotenv import load_dotenv
from constants import GREEN_TIME, MAX_STEPS, YELLOW_TIME
from network import get_net_data
from utils import get_args, get_green_phases, get_phase_lanes, get_sumo_cmd, get_tl_incoming_lanes


def get_green_phase_lanes(net_data, tl_ids, phase_lanes, green_phases):
    max_pressure_lanes = {tl_id: {} for tl_id in tl_ids}
    for tl_id in tl_ids:
        for green_phase in green_phases[tl_id]:
            inc_lanes = set()
            out_lanes = set()
            for lane in phase_lanes[tl_id][green_phase]:
                inc_lanes.add(lane)
                for outgoing_lane in net_data["lane_data"][lane]["outgoing"]:
                    out_lanes.add(outgoing_lane)

            max_pressure_lanes[tl_id][green_phase] = {
                "inc": inc_lanes,
                "out": out_lanes,
            }
    return max_pressure_lanes


def get_phase_with_max_pressure(phase_lanes, green_phases):
    phase_pressures = {}

    for phase in green_phases:
        inc_lanes = phase_lanes[phase]["inc"]
        out_lanes = phase_lanes[phase]["out"]
        incoming_pressure = 0
        outgoing_pressure = 0
        for lane in inc_lanes:
            incoming_pressure += traci.lane.getLastStepVehicleNumber(lane)

        for lane in out_lanes:
            outgoing_pressure += traci.lane.getLastStepVehicleNumber(lane)

        phase_pressures[phase] = incoming_pressure - outgoing_pressure

    phase_pressures = [
        (key, value)
        for key, value in sorted(
            phase_pressures.items(), key=lambda item: item[1], reverse=True
        )
    ]

    return phase_pressures[0][0]


def main():
    load_dotenv()
    args = get_args()
    sumo_cmd = get_sumo_cmd(args)

    traci.start(sumo_cmd)

    net_data = get_net_data(args.scenario)
    tl_ids = traci.trafficlight.getIDList()
    tl_green_phases = get_green_phases(tl_ids)
    tl_phase_lanes = get_phase_lanes(net_data, tl_ids, tl_green_phases)
    tl_green_phase_lanes = get_green_phase_lanes(
        net_data, tl_ids, tl_phase_lanes, tl_green_phases
    )
    tl_cur_phase = {
        tl_id: traci.trafficlight.getRedYellowGreenState(tl_id) for tl_id in tl_ids
    }
    tl_pending_green_phase = {tl_id: "" for tl_id in tl_ids}

    tl_incoming_lanes = get_tl_incoming_lanes(net_data, tl_ids)

    time_to_action = {}

    for tl_id in tl_ids:
        time_to_action[tl_id] = 0

    total_waiting_time = 0
    total_vehicles = set()

    step = 0
    while step < MAX_STEPS:
        vehicles = traci.vehicle.getIDList()
        total_vehicles.update(set(vehicles))
        if step > 1000 and traci.vehicle.getIDCount() == 0:
            print("Simulation ended at:", step)
            break
        for tl_id in tl_ids:
            for lane in tl_incoming_lanes[tl_id]:
                total_waiting_time += traci.lane.getLastStepHaltingNumber(lane)
            if time_to_action[tl_id] != 0:
                time_to_action[tl_id] -= 1
            else:
                if tl_pending_green_phase[tl_id]:
                    traci.trafficlight.setRedYellowGreenState(
                        tl_id, tl_pending_green_phase[tl_id]
                    )
                    tl_cur_phase[tl_id] = tl_pending_green_phase[tl_id]
                    time_to_action[tl_id] = GREEN_TIME
                    tl_pending_green_phase[tl_id] = ""
                    continue

                new_phase = get_phase_with_max_pressure(
                    tl_green_phase_lanes[tl_id], tl_green_phases[tl_id]
                )

                if new_phase != tl_cur_phase[tl_id]:
                    yellow_phase = (
                        tl_cur_phase[tl_id].replace("G", "y").replace("g", "y")
                    )
                    traci.trafficlight.setRedYellowGreenState(tl_id, yellow_phase)
                    tl_pending_green_phase[tl_id] = new_phase
                    time_to_action[tl_id] = YELLOW_TIME

        traci.simulationStep()
        step += 1

    traci.close()

    print(f"Total waiting time: {total_waiting_time}, Total vehicles passed: {len(total_vehicles)}")

if __name__ == "__main__":
    main()
