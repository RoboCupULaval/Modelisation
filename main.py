import time
import random

import scipy.fftpack as fftp
import matplotlib.pyplot as plt

from RULEngine.Command import command
from RULEngine.Communication import udp_server
from RULEngine.Communication.vision import Vision
from RULEngine.Game.Player import Player
from RULEngine.Game.Team import Team
from RULEngine.Util.Position import Position


COMMAND_HOST = "127.0.0.1"
COMMAND_PORT = 20011
VISION_HOST = "224.5.23.2"
VISION_PORT = 10020

FPS = 1/60


gr_sim_cmd_sender = udp_server.GrSimCommandSender(COMMAND_HOST, COMMAND_PORT)
gr_sim_debug_sender = udp_server.GrSimDebugSender(COMMAND_HOST, COMMAND_PORT)
vision = Vision(VISION_HOST, VISION_PORT)

frames = []
blue_team = Team(False)
yellow_team = Team(True)


def main():
    print("Debut test d'asservissement")

    while not vision.get_latest_frame():
        time.sleep(0.01)
        print("En attente d'une image de la vision.")
    frames.append(vision.get_latest_frame())

    init_field()

    default_player = blue_team.players[0]
    test_vel = Position(1.0, 0)
    cmd = command.MoveTo(default_player, test_vel)
    stop_cmd = command.MoveTo(default_player, Position())

    print("Envoi commande x pure")
    gr_sim_cmd_sender.send_command(cmd)
    print("Attente 1 seconde")
    current_timestamp = get_time()
    cmd_timestamp = current_timestamp
    while current_timestamp - cmd_timestamp < 1:
        latest_frame = vision.get_latest_frame()
        if latest_frame is not frames[-1]:
            frames.append(vision.get_latest_frame())
        current_timestamp = get_time()

    print("Arret du robot")
    gr_sim_cmd_sender.send_command(stop_cmd)

    sim_tim = []
    robot_x = []
    robot_y = []
    for frame in frames:
        sim_tim.append(frame.detection.t_capture)
        robot = frame.detection.robots_blue[0]
        robot_x.append(robot.x)
        robot_y.append(robot.y)

    print("Temps ecoule (grsim): {}".format(get_time() - get_init_time()))


def init_field():
    print("Déplacement robot au centre")
    for idx in range(6):
        blue_team.players[idx] = Player(blue_team, idx)
        yellow_team.players[idx] = Player(yellow_team, idx)

    out_fields_cmd = []
    for player in yellow_team.players.values():
        cmd = command.MoveTo(player, Position(0, random.random() + 6))
        out_fields_cmd.append(cmd)
    for player in blue_team.players.values():
        cmd = command.MoveTo(player, Position(0, random.random() + 6))
        out_fields_cmd.append(cmd)

    for cmd in out_fields_cmd:
        gr_sim_debug_sender.send_command(cmd)
    default_player = blue_team.players[0]
    center_pos = Position(0, 0)
    center_cmd = command.MoveTo(default_player, center_pos)
    gr_sim_debug_sender.send_command(center_cmd)
    gr_sim_debug_sender.place_ball(Position(1, 2))


def get_init_time() -> float:
    return frames[0].detection.t_capture


def get_time() -> float:
    return frames[-1].detection.t_capture


if __name__ == "__main__":
    main()
