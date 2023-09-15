import os
import pathlib
import subprocess



url =pathlib.Path("user_data/conf/")
conf_files = pathlib.Path.glob(url,"*.json")
prefix_path = "/home/al/source/freqtrade/"
# print(list(conf_files))
for conf_file in conf_files:
    config_name = prefix_path + conf_file.as_posix()
    cmd = ["freqtrade", "trade", "--config", f"{config_name}","--strategy","PriceSpikeStrategy"]
    subprocess.Popen(cmd)


