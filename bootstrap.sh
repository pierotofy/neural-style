#!/bin/bash

# To execute run:
# wget -O - https://raw.githubusercontent.com/pierotofy/neural-style/master/bootstrap.sh | bash

me=$(whoami)
sudo echo "$me ALL=(ALL) NOPASSWD: /sbin/poweroff, /sbin/reboot, /sbin/shutdown" >> /etc/sudoers

# Install neural style and dependencies on a paperspace ML-box
pip install requests
git clone https://github.com/pierotofy/neural-style
cd neural-style
luarocks install loadcaffe
./models/download_models.sh
