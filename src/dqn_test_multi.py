import os
import traci
import numpy as np
import tensorflow as tf
from dotenv import load_dotenv
from dqn_train import MAX_EPISODES
from dqn_utils import (
    get_cur_waiting_time,
    get_state,
    set_green_phase,
    set_yellow_phase,
)
from network import get_net_data
from utils import (
    get_args,
    get_incoming_vehicles,
    get_green_phases,
    get_phases,
    get_sumo_cmd,
)
from constants import GREEN_TIME, MAX_STEPS, YELLOW_TIME
from dqn_network import QNetwork


def main(model_id):
    load_dotenv()
    args = get_args()
    sumo_cmd = get_sumo_cmd(args)

    traci.start(sumo_cmd)

    net_data = get_net_data(args.scenario)

    tl_ids = traci.trafficlight.getIDList()
    tl_phases = get_phases(tl_ids)
    tl_green_phases = get_green_phases(tl_ids)
    tl_incoming_edges = {
        tl_id: net_data["intersection"][tl_id]["incoming"] for tl_id in tl_ids
    }

    tl_incoming_lanes = {}

    for tl_id in tl_incoming_edges:
        tl_edges = tl_incoming_edges[tl_id]
        tl_incoming_lanes[tl_id] = [
            net_data["edge_data"][edgeId]["lanes"] for edgeId in tl_edges
        ]

    tl_incoming_lanes = {
        tl_id: np.sort(np.concatenate(tl_incoming_lanes[tl_id]).flatten())
        for tl_id in tl_incoming_lanes
    }

    tl_incoming_vehicles = {tl_id: [] for tl_id in tl_ids}
    tl_waiting_times = {tl_id: 0 for tl_id in tl_ids}

    q_networks = {}
    for tl_id in tl_ids:
        state_size = len(get_state(tl_incoming_lanes, tl_id))
        action_size = len(tl_green_phases[tl_id])
        q_networks[tl_id] = QNetwork(state_size, action_size)
        q_networks[tl_id].model = tf.keras.models.load_model(
            os.path.join(
                os.path.dirname(__file__),
                f"models/{args.scenario}/{tl_id}/model_episode_{model_id}",
            )
        )

    step = 0
    time_to_action = {}
    prev_actions = {}
    pending_actions = {}

    for tl_id in tl_ids:
        time_to_action[tl_id] = 0

    total_reward = 0
    total_waiting_time = 0
    total_vehicles = set()

    while step < MAX_STEPS:
        vehicles = traci.vehicle.getIDList()
        total_vehicles.update(set(vehicles))
        # if step > 1000 and len(vehicles) == 0:
        #     print("Simulation ended at:", step)
        #     break
        for tl_id in tl_ids:
            for lane in tl_incoming_lanes[tl_id]:
                total_waiting_time += traci.lane.getLastStepHaltingNumber(lane)

            if time_to_action[tl_id] == 0:
                if step == 0:
                    state = get_state(tl_incoming_lanes, tl_id)
                    action = q_networks[tl_id].predict(state)
                    prev_actions[tl_id] = 0
                    continue

                # yellow phase ended
                if tl_id in pending_actions and pending_actions[tl_id] is not None:
                    action = pending_actions[tl_id]
                    time_to_action[tl_id] = GREEN_TIME
                    set_green_phase(tl_id, tl_phases, tl_green_phases[tl_id][action])
                    pending_actions[tl_id] = None
                else:
                    cur_waiting_time = get_cur_waiting_time(
                        tl_incoming_lanes[tl_id], tl_incoming_vehicles[tl_id]
                    )
                    reward = tl_waiting_times[tl_id] - cur_waiting_time
                    if reward < 0:
                        total_reward += reward

                    tl_waiting_times[tl_id] = cur_waiting_time

                    state = get_state(tl_incoming_lanes, tl_id)

                    tl_incoming_vehicles[tl_id] = get_incoming_vehicles(
                        tl_incoming_lanes[tl_id]
                    )
                    action = q_networks[tl_id].predict(state)
                    # print(f'step: {step}, state: {state}, action: {action}, reward: {reward}, total reward: {total_reward}')

                    if prev_actions[tl_id] != action:
                        set_yellow_phase(
                            tl_id,
                            tl_phases,
                            tl_green_phases[tl_id][prev_actions[tl_id]],
                        )
                        time_to_action[tl_id] = YELLOW_TIME
                        prev_actions[tl_id] = action
                        pending_actions[tl_id] = action
                    else:
                        time_to_action[tl_id] = GREEN_TIME
            else:
                time_to_action[tl_id] -= 1

        traci.simulationStep()
        step += 1

    traci.close()
    print(
        f"Total waiting time: {total_waiting_time}, Total reward: {total_reward}, Total vehicles passed: {len(total_vehicles)}"
    )


if __name__ == "__main__":
    main(29)
