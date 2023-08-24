import os
import random
import time
from matplotlib import pyplot as plt
import traci
import numpy as np
import tensorflow as tf
from dotenv import load_dotenv
from dqn_utils import (
    clean_models,
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
    get_tl_incoming_lanes,
)
from constants import GREEN_TIME, MAX_EPISODES, MAX_STEPS, YELLOW_TIME
from dqn_network import QNetwork

BATCH_SIZE = 100
GAMMA = 0.75
REPLAY_MEMORY_SIZE = 50000


def main():
    print(tf.__version__)
    print(tf.test.gpu_device_name())

    load_dotenv()
    args = get_args()
    sumo_cmd = get_sumo_cmd(args)

    traci.start(sumo_cmd)

    net_data = get_net_data(args.scenario)

    tl_ids = traci.trafficlight.getIDList()
    tl_phases = get_phases(tl_ids)
    tl_green_phases = get_green_phases(tl_ids)

    tl_incoming_lanes = get_tl_incoming_lanes(net_data, tl_ids)

    state_size = len(get_state(tl_incoming_lanes, tl_ids[0]))
    action_size = len(tl_green_phases[tl_ids[0]])

    traci.close()

    q_network = QNetwork(state_size, action_size)

    replay_memory = []
    total_rewards = []

    clean_models(args.scenario)

    for episode in range(1, MAX_EPISODES + 1):
        prev_actions = {}
        prev_states = {}
        pending_actions = {}
        epsilon = 1.0 - (episode / MAX_EPISODES)
        total_reward = 0
        time_to_action = {}
        step = 0

        tl_waiting_times = {tl_id: 0 for tl_id in tl_ids}
        tl_incoming_vehicles = {tl_id: [] for tl_id in tl_ids}

        for tl_id in tl_ids:
            time_to_action[tl_id] = 0

        traci.start(sumo_cmd)
        sim_start = time.time()

        while step < MAX_STEPS:
            for tl_id in tl_ids:
                if time_to_action[tl_id] == 0:
                    if step == 0:
                        state = get_state(tl_incoming_lanes, tl_id)
                        action = q_network.act(state, epsilon)
                        prev_states[tl_id] = state
                        prev_actions[tl_id] = 0
                        continue

                    # yellow phase ended
                    if tl_id in pending_actions and pending_actions[tl_id] is not None:
                        action = pending_actions[tl_id]
                        time_to_action[tl_id] = GREEN_TIME
                        set_green_phase(
                            tl_id, tl_phases, tl_green_phases[tl_id][action]
                        )
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

                        experience = {
                            "state": prev_states[tl_id],
                            "action": action,
                            "reward": reward,
                            "next_state": state,
                        }
                        # print(f'step: {step}, state: {experience["state"]}, action: {action}, reward: {reward}, next state: {experience["next_state"]}')

                        replay_memory.append(experience)
                        if len(replay_memory) > REPLAY_MEMORY_SIZE:
                            replay_memory.pop(0)

                        tl_incoming_vehicles[tl_id] = get_incoming_vehicles(
                            tl_incoming_lanes[tl_id]
                        )
                        action = q_network.act(state, epsilon)

                        prev_states[tl_id] = state
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

        sim_end = time.time()

        if len(replay_memory) > BATCH_SIZE:
            for i in range(20):
                batch = random.sample(replay_memory, BATCH_SIZE)
                states = np.array([experience["state"] for experience in batch])
                actions = [experience["action"] for experience in batch]
                rewards = [experience["reward"] for experience in batch]
                next_states = [experience["next_state"] for experience in batch]

                targets = q_network.model.predict(states, verbose=0)
                q_values = q_network.model.predict(next_states, verbose=0)
                max_q_values = np.amax(q_values, axis=1)

                for i in range(BATCH_SIZE):
                    targets[i, actions[i]] = rewards[i] + GAMMA * max_q_values[i]

                q_network.model.fit(
                    states, targets, epochs=1, batch_size=BATCH_SIZE, verbose=0
                )

        train_end = time.time()
        print(
            f"Episode {episode}/{MAX_EPISODES}, Total Reward: {total_reward:.0f}, ",
            f"Epsilon: {round(epsilon, 2)}, Memory size: {len(replay_memory)}, ",
            f"Sim time: {sim_end-sim_start:.0f}s, ",
            f"Training time: {train_end - sim_end:.0f}s"
        )
        total_rewards.append(total_reward)

        q_network.model.save(
            os.path.join(os.path.dirname(__file__), f"models/model_episode_{episode}")
        )

        traci.close()

    episodes = list(range(1, MAX_EPISODES + 1))

    plt.plot(episodes, total_rewards)
    plt.ylabel("Total reward")
    plt.xlabel("Episode")
    fig = plt.gcf()
    fig.savefig(
        os.path.join(os.path.dirname(__file__), "./plots/total_reward_training.png")
    )
    plt.close("all")


if __name__ == "__main__":
    main()
