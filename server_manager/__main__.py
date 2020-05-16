import argparse
import sys

from .src.dataframe import get_dataframe, get_mode
from .src.player import Player
from .src.set_mode import set_mode
from .src.utils import Memory, str2bool


def parse_args() -> dict:
    parser = argparse.ArgumentParser("online-mode-manager")
    subparsers = parser.add_subparsers(dest="command")

    online_mode_parser = subparsers.add_parser("online-mode")
    online_mode_parser.add_argument("online-mode", type=str2bool, nargs="?")

    subparsers.add_parser("list")
    subparsers.add_parser("data")
    subparsers.add_parser("whitelist")

    Memory.set_parser(parser)
    return vars(parser.parse_args())


def main():
    args = parse_args()
    command = args["command"]

    if command == "online-mode":
        online_mode = args["online-mode"]
        set_mode(mode=online_mode)
        print(f"Set online-mode to {online_mode}")
        sys.exit()

    if command == "data":
        print(get_dataframe())
        sys.exit()

    if command == "list":
        players = Player.generate()
        for player in players:
            print(
                " - %s - %s - %s"
                % (player.username, get_mode(player.uuid), player.uuid)
            )
        sys.exit()


if __name__ == "__main__":
    main()