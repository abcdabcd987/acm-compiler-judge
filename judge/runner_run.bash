cd /testrun

echo "  = nasm =" >stderr.txt
nasm -felf64 program.asm 2>>stderr.txt 1>&2
EC=$?
if [ "$EC" -ne "0" ]; then
    echo -10 > exitcode.txt
    echo 0 > time_us.txt
    exit 1
fi

echo "  = gcc =" >>stderr.txt
gcc -O0 -o program program.o 2>>stderr.txt 1>&2
EC=$?
if [ "$EC" -ne "0" ]; then
    echo -20 > exitcode.txt
    echo 0 > time_us.txt
    exit 1
fi

echo "  = program =" >>stderr.txt
st=$(date +%s%N)
./program <input.txt 1>stdout.txt 2>>stderr.txt
EC=$?
ed=$(date +%s%N)
dt=$((($ed - $st)/1000))
echo "$EC" >exitcode.txt
echo "$dt" >time_us.txt