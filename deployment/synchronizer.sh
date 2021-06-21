#!/bin/bash

deployed_sha_sum=`shasum -a 256 /usr/local/etc/tac_plus.cfg | awk -F" " '{print $1}'`
to_be_deployed_sha_sum=`shasum -a 256 /var/tmp/tac_plus.cfg | awk -F" " '{print $1}'`

if [ "$deployed_sha_sum" != "$to_be_deployed_sha_sum" ]
then
	echo "Deploying the configuration file..."
	cp -rv /var/tmp/tac_plus.cfg /usr/local/etc/tac_plus.cfg
	/etc/init.d/tac_plus stop
	/etc/init.d/tac_plus start
else
	echo "Configurations are the same. Skipping..."
fi
