cd /compiler
st=$(date +%s%N)
bash $1.bash < /testrun/program.txt 1> /testrun/stdout.txt 2> /testrun/stderr.txt
echo $? > /testrun/exitcode.txt
ed=$(date +%s%N)
dt=$((($ed - $st)/1000))
echo "$dt" > /testrun/time_us.txt