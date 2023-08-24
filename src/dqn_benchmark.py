import os
import matplotlib.pyplot as plt
from dqn_test import run_test
from dqn_train import MAX_EPISODES


if __name__ == "__main__":
    results = []
    waiting_times = []
    rewards = []

    for episode in range(1, MAX_EPISODES + 1):
        result = run_test(episode)

        print(
            f"Episode: {episode}, Total waiting time: {result['total_waiting_time']}, Total reward: {result['total_reward']}"
        )

        results.append(result)

    for result in results:
        waiting_times.append(result["total_waiting_time"])
        rewards.append(result["total_reward"])

    episodes = list(range(1, MAX_EPISODES + 1))

    plt.plot(episodes, waiting_times)
    plt.ylabel("Total waiting time")
    plt.xlabel("Episode")
    fig = plt.gcf()
    fig.savefig(os.path.join(os.path.dirname(__file__), "./plots/total_waiting_time_testing.png"))
    plt.close("all")

    plt.plot(episodes, rewards)
    plt.ylabel("Total reward")
    plt.xlabel("Episode")
    fig = plt.gcf()
    fig.savefig(os.path.join(os.path.dirname(__file__), "./plots/total_reward_testing.png"))
    
    plt.close("all")
