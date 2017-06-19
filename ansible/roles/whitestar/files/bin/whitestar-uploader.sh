#!/bin/sh

while true; do
	rsync --remove-source-files -av /var/log/archive whitestar@172.20.171.116:log
	sleep 120
done
 
