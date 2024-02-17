#!/bin/bash
sudo systemctl stop autocorrect.service
sudo systemctl disable autocorrect.service
sudo rm /usr/local/sbin/autocorrect
sudo rm /etc/systemd/system/autocorrect.service
echo "Autocorrect service is successfully removed." 

