#! /bin/bash

start=2
end=8
filePrefix="/home/ubuntu/ntp_logs/ntp_userv"

time=`date +'%s'`
opFile="op_ntp""$time"".log"
echo "time: $time opFile: $opFile"
#exit
echo "" > $opFile
for((i=start;i<=end;i++))
do
	ls -ltr "$filePrefix"$i".log"
        ls -ltr "$filePrefix"$i".log" >> $opFile
	cat "$filePrefix"$i".log" >> $opFile
        echo "" >> $opFile
done

filePrefix="/home/ubuntu/ntp_logs/ntp_"
ls -ltr "$filePrefix""userv1.log" >> $opFile
cat "$filePrefix""userv1.log" >> $opFile
echo "" >> $opFile


echo "This is the body" | mail -s "NTP update `date`" -A $opFile gsomashekar@cs.stonybrook.edu
