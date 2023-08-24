import traci
from dotenv import load_dotenv
from constants import MAX_STEPS
from network import get_net_data
from utils import get_sumo_cmd, get_args, get_tl_incoming_lanes

if __name__ == "__main__":
    load_dotenv()
    args = get_args()
    sumo_cmd = get_sumo_cmd(args)

    traci.start(sumo_cmd)

    net_data = get_net_data(args.scenario)
    tl_ids = traci.trafficlight.getIDList()
    tl_incoming_lanes = get_tl_incoming_lanes(net_data, tl_ids)

    total_waiting_time = 0
    step = 0
    total_vehicles = set()

    while step < MAX_STEPS:
        vehicles = traci.vehicle.getIDList()
        total_vehicles.update(set(vehicles))
        if step > 1000 and len(vehicles) == 0:
            print("Simulation ended at:", step)
            break
        for tl_id in tl_ids:
            for lane in tl_incoming_lanes[tl_id]:
                total_waiting_time += traci.lane.getLastStepHaltingNumber(lane)

        traci.simulationStep()
        step += 1

    print(f"Total waiting time: {total_waiting_time}, Total vehicles passed: {len(total_vehicles)}")
    traci.close()
