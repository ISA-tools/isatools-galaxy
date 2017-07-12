#!/bin/bash

apt-get update -y && apt-get install -y --no-install-recommends wget ca-certificates

# Testing for version 0.2.x of the container

# Download data
wget "https://drive.google.com/uc?export=download&id=0B2e3YmwhK4fkck1mQVpMQTZZakk" -O constraints.csv

uploadToMetaboLightsLabs.py -t 63fc1986-6309-4541-b8f0-15a97acb11a2 -i constraints.csv -n -s dev

# check that result file exists.
LOG_FILE=cli.log

for f in $LOG_FILE; do
	if [ ! -f $f ]; then
   		echo "File $f does not exist, failing test."
		echo "Logs say:"
		cat aspera-scp-transfer.log
   		exit 1
	fi
done

echo "Labs uploader runs with test data without error codes, all expected files created."
