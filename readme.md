# Online Judge for Compiler Course @ ACM Honored Class, SJTU

## Setup Guide for the Core Server

```bash
sudo apt-get install -y git python-pip postgresql postgresql-server-dev-9.3 libpq-dev python-dev python-setuptools gunicorn tmux
sudo -H -u postgres psql
postgres=# CREATE USER compiler2017 WITH PASSWORD 'mypassword';
postgres=# CREATE DATABASE compiler2017;
postgres=# GRANT ALL PRIVILEGES ON DATABASE compiler2017 to compiler2017;
postgres=# \q
git clone https://github.com/abcdabcd987/acm-compiler-judge.git
cd acm-compiler-judge
sudo -H pip install -r requirements.txt
cp settings.example.py settings.py
vim settings.py
./maintenance.py initdb
./maintenance.py initdb <random_token>
./maintenance.py makedirs
```

## Setup Guide for Judge Server

```bash
sudo apt-get -y install apt-transport-https ca-certificates curl python-dev python-setuptools software-properties-common tmux
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y git python-pip docker-ce libpq-dev python-dev
sudo usermod -aG docker $USER

git clone https://github.com/abcdabcd987/acm-compiler-judge.git
cd acm-compiler-judge/judge/docker-image
docker build -t acm-compiler-judge:latest -f production.Dockerfile .

cd ../..
sudo -H pip install -r requirements.txt
cp settings.example.py settings.py
vim settings.py
./maintenance.py makedirs
```

You can add `autostart_tmux_judge.sh` to `/etc/rc.local` to make judge autostart. For example,

```bash
su - abcdabcd987 -c "nohup /home/abcdabcd987/acm-compiler-judge/autostart_tmux_judge.sh > /dev/null 2>&1 &"
```

## Run Core Server

```bash
# run core
./core/repo_watcher.py
./core/testrun_watcher.py

# run web
gunicorn -b 0.0.0.0:6002 core.core:app  # for production run
./core/core.py                          # for debug run

# maintenance
./maintenance.py
```

## Run Judge Server

```bash
./judge/judge.py
```

## Final Rejudge

```bash
# core: judge all
./maintenance.py final_rejudge final/submit.csv final/rejudge.csv

# judge: disable cpu frequency scaling
for CPUFREQ in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
do 
    echo performance | sudo tee $CPUFREQ
done
grep MHz /proc/cpuinfo

# judge: disable Intel Turbo Boost on core0-7
sudo apt-get install msr-tools
sudo modprobe msr
sudo wrmsr -p0 0x1a0 0x4000850089
sudo wrmsr -p1 0x1a0 0x4000850089
sudo wrmsr -p2 0x1a0 0x4000850089
sudo wrmsr -p3 0x1a0 0x4000850089
sudo wrmsr -p4 0x1a0 0x4000850089
sudo wrmsr -p5 0x1a0 0x4000850089
sudo wrmsr -p6 0x1a0 0x4000850089
sudo wrmsr -p7 0x1a0 0x4000850089

# core: generate final result
./maintenance.py generate_final_result final/rejudge.csv core/static/final/v1
vim settings.py
```

## Some tips on `~/.ssh/config`

```
Host *
    StrictHostKeyChecking no
Host bitbucket.org # if GFWed, you might want to use a proxy
    ProxyCommand=socat - PROXY:your-proxy-host:%h:%p,proxyport=your-proxy-port
```
