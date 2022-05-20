#! /bin/bash

#.conf file has been copied by the .py script. Restart to update the server
#sudo /etc/init.d/ntp stop
host=`hostname -I | cut -d " " -f1`
file="ntp_$host.log"
echo "" > $file
for((i=1;i<=16;i++));
do
  sudo ntpq -c lpeer >> $file; 
  sudo service ntp stop;
  sudo ntpd -gq; #-g forces to ntpd to synchronize the local clock with the server clock irrespective of the offset. 
  sudo service ntp start;  
  sleep 32;
done

#scp -i ~/compass.key ntp_*.log ubuntu@$ntp_server:~/ntp_logs/
