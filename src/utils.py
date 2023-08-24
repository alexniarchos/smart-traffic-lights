import argparse
import os
import numpy as np
import traci

from constants import MAX_STEPS


def get_phase_lanes(net_data, tl_ids, tl_green_phases):
    phase_lanes = {tl_id: {} for tl_id in tl_ids}
    for tl_id in tl_ids:
        phase_lanes[tl_id] = {state: [] for state in tl_green_phases[tl_id]}
        for state in tl_green_phases[tl_id]:
            green_lanes = set()
            red_lanes = set()
            for s in range(len(state)):
                if state[s] == "g" or state[s] == "G":
                    green_lanes.add(net_data["intersection"][tl_id]["tlsindex"][s])
                elif state[s] == "r":
                    red_lanes.add(net_data["intersection"][tl_id]["tlsindex"][s])

            # some movements are on the same lane, removes duplicate lanes
            pure_green = [l for l in green_lanes if l not in red_lanes]
            if len(pure_green) == 0:
                phase_lanes[tl_id][state] = list(set(green_lanes))
            else:
                phase_lanes[tl_id][state] = list(set(pure_green))
    return phase_lanes


def get_green_phases(tl_ids):
    green_phases = {tl_id: [] for tl_id in tl_ids}
    for tl_id in tl_ids:
        cur_program = int(traci.trafficlight.getProgram(tl_id))
        green_phases[tl_id] = []
        for phase in traci.trafficlight.getAllProgramLogics(tl_id)[cur_program].phases:
            if "y" not in phase.state and ("G" in phase.state or "g" in phase.state):
                green_phases[tl_id].append(phase.state)
    return green_phases


def get_phases(tl_ids):
    phases = {tl_id: [] for tl_id in tl_ids}
    for tl_id in tl_ids:
        cur_program = int(traci.trafficlight.getProgram(tl_id))

        phases[tl_id] = [
            phase.state
            for phase in traci.trafficlight.getAllProgramLogics(tl_id)[
                cur_program
            ].phases
        ]

    return phases


def get_incoming_vehicles(incoming_lanes):
    vehicles = []

    for lane in incoming_lanes:
        vehicles.extend(traci.lane.getLastStepVehicleIDs(lane))

    return vehicles


def get_tl_incoming_lanes(net_data, tl_ids):
    tl_incoming_lanes = {}

    tl_incoming_edges = {
        tl_id: net_data["intersection"][tl_id]["incoming"] for tl_id in tl_ids
    }

    for tl_id in tl_incoming_edges:
        tl_edges = tl_incoming_edges[tl_id]
        tl_incoming_lanes[tl_id] = [
            net_data["edge_data"][edgeId]["lanes"] for edgeId in tl_edges
        ]

    tl_incoming_lanes = {
        tl_id: np.sort(np.concatenate(tl_incoming_lanes[tl_id]).flatten())
        for tl_id in tl_incoming_lanes
    }

    return tl_incoming_lanes


def get_sumo_cmd(args):
    sumo_bin = "sumo-gui" if args.gui else "sumo"

    return [
        f'{os.getenv("SUMO_BINARY")}/{sumo_bin}',
        "-c",
        os.path.join(
            os.path.dirname(__file__), f"./configs/comparative-study/{args.scenario}/index.sumocfg"
        ),
        "--start",
        "--no-step-log",
        "--no-warnings",
        "--quit-on-end",
        "--waiting-time-memory",
        str(MAX_STEPS),
        # "-d",
        # "200",
        # "--step-length",
        # "0.2",
    ]


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gui", action="store_true", help="show sumo-gui")
    parser.add_argument(
        "--scenario",
        choices=[
            "3x3-grid",
            "4x4-grid",
            "arterial-road",
            "real-world",
            "single-intersection",
            "double-intersection",
            "unbalanced-intersection",
            "arterial-greenwave",
            "arterial-maxband",
            "single-test"
        ],
        default="3x3-grid",
        help="sumo config scenario",
    )

    args = parser.parse_args()
    return args
