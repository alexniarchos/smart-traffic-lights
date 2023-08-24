import os
import sumolib


def get_net_data(net_config):
    net = sumolib.net.readNet(
        os.path.join(os.path.dirname(__file__), f"./configs/comparative-study/{net_config}/net.xml")
    )

    edge_data = get_edge_data(net)
    lane_data = get_lane_data(net, edge_data)
    intersection = get_node_data(net)

    return {
        "edge_data": edge_data,
        "lane_data": lane_data,
        "intersection": intersection,
    }


def get_edge_data(net):
    edges = net.getEdges()
    edge_data = {str(edge.getID()): {} for edge in edges}

    for edge in edges:
        edge_id = str(edge.getID())
        edge_data[edge_id]["lanes"] = [str(lane.getID()) for lane in edge.getLanes()]

    return edge_data


def get_lane_data(net, edge_data):
    lane_ids = []
    for edge in edge_data:
        lane_ids.extend(edge_data[edge]["lanes"])

    lanes = [net.getLane(lane) for lane in lane_ids]
    lane_data = {lane: {} for lane in lane_ids}

    for lane in lanes:
        lane_id = lane.getID()
        lane_data[lane_id]["edge"] = str(lane.getEdge().getID())
        lane_data[lane_id]["outgoing"] = []

        for conn in lane.getOutgoing():
            out_id = str(conn.getToLane().getID())
            lane_data[lane_id]["outgoing"].append(out_id)
        lane_data[lane_id]["incoming"] = []

    # determine incoming lanes using outgoing lanes data
    for lane in lane_data:
        for inc in lane_data:
            if lane == inc:
                continue
            else:
                if inc in lane_data[lane]["outgoing"]:
                    lane_data[inc]["incoming"].append(lane)

    return lane_data


def get_node_data(net):
    nodes = net.getNodes()
    node_data = {node.getID(): {} for node in nodes}

    for node in nodes:
        node_id = node.getID()

        node_data[node_id]["incoming"] = set(
            str(edge.getID()) for edge in node.getIncoming()
        )
        node_data[node_id]["outgoing"] = set(
            str(edge.getID()) for edge in node.getOutgoing()
        )
        node_data[node_id]["tlsindex"] = {
            conn.getTLLinkIndex(): str(conn.getFromLane().getID())
            for conn in node.getConnections()
        }

    intersection = {
        str(node): node_data[node]
        for node in node_data
        if "traffic_light" in net.getNode(node).getType()
    }

    return intersection
