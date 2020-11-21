import sys
from chariot import server_start

# if len(sys.argv) != 2:
#     print(f"{sys.argv[0]} config.yaml")
#
# server_start(sys.argv[1])
server_start("/tmp/pycharm_project_72/config.yaml")
