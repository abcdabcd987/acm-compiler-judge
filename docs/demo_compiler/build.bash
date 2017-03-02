# this script is called when the judge is building your compiler.
# no argument will be passed in.
#
# our demo simply calls g++.
# in order to do that, we need objconv,
# therefore, let's build objconv instead.
# and let's print the version of g++, just for fun.

set -e
cd "$(dirname "$0")"
unzip objconv.zip
g++ -o /usr/bin/objconv -O2 objconv-master/src/*.cpp
g++ --version
