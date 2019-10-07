#!/bin/bash
sudo apt-get install kvm
sudo apt-get install python-libvirt -y
sudo apt-get install openssh-server open-ssh-client
sudo apt-get install pip
pip install Flask
python ../src/script.py ../src/pm_file ../src/image_file ../src/flavor_file
