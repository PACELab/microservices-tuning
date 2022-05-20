init_servers=$1
mkdir -p /home/ubuntu/ntp_logs

if [ $init_servers == 1 ];
then
  while IFS=, read -r host yaml
  do
   #copying and moving as the user ubuntu doesn't have permission to write. TODO: of course, there is a way to do it in a single demand. Find it. 
   scp -i /home/ubuntu/compass.key ntp.conf ubuntu@$host:~/
   ssh -ni /home/ubuntu/compass.key ubuntu@$host "sudo mv ~/ntp.conf /etc/"
  done < $2

  while IFS=, read -r host yaml
  do
   scp -i /home/ubuntu/compass.key ntpSync.sh ubuntu@$host:~/
   ssh -ni /home/ubuntu/compass.key ubuntu@$host "nohup /home/ubuntu/ntpSync.sh  > /dev/null 2>&1  " &
  done < $2
sleep 550
fi;

# When $1 == 1, this is to check the difference after synchornizaion process above is complete
# When $1 == 0, this implies the script is being called after the experimetns are complete. Just to check the offset around the time the offsets are complete.
while IFS=, read -r host yaml
do
  ssh -ni /home/ubuntu/compass.key ubuntu@$host  "sudo ntpq -c lpeer >> ntp_$host.log"; 
  scp -i /home/ubuntu/compass.key ubuntu@$host:~/ntp_*.log ~/ntp_logs/
done < $2

sleep 2

time=`date +'%s'`
opFile="op_ntp""$time"".log"
echo "time: $time opFile: $opFile"
echo "" > $opFile

while IFS=, read -r host yaml
do
    file="/home/ubuntu/ntp_logs/ntp_$host.log"
    ls -ltr $file >> $opFile
    cat $file >> $opFile
    echo "" >> $opFile
done < $2


echo "This is the body" | mail -s "NTP update `date`" -A $opFile gsomashekar@cs.stonybrook.edu
