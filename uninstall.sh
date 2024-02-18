#!/bin/bash
sudo systemctl stop autocorrect.service
sudo systemctl disable autocorrect.service
sudo rm /usr/local/sbin/autocorrect
sudo rm /etc/systemd/system/autocorrect.service
sudo rm -rf /etc/autocorrect/
echo "Autocorrect service is successfully removed." 

