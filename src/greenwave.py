import traci
from dotenv import load_dotenv
from constants import MAX_STEPS
from network import get_net_data
from utils import get_args, get_sumo_cmd, get_tl_incoming_lanes


def main():
    load_dotenv()
    args = get_args()
    sumo_cmd = get_sumo_cmd(args)

    traci.start(sumo_cmd)

    tl_ids = traci.trafficlight.getIDList()
    net_data = get_net_data(args.scenario)

    tl_incoming_lanes = get_tl_incoming_lanes(net_data, tl_ids)

    total_waiting_time = 0
    step = 0
    while step < MAX_STEPS:
        for tl_id in tl_ids:
            for lane in tl_incoming_lanes[tl_id]:
                total_waiting_time += traci.lane.getLastStepHaltingNumber(lane)

        traci.simulationStep()
        step += 1

    traci.close()

    print(f"Total waiting time: {total_waiting_time}")


if __name__ == "__main__":
    main()
