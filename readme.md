# Online Judge for Compiler Course @ ACM Honored Class, SJTU

## Setup Guide for the Core Server

```bash
sudo apt-get install -y git python-pip postgresql postgresql-server-dev-9.3 libpq-dev python-dev python-setuptools gunicorn
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
sudo apt-get -y install apt-transport-https ca-certificates curl python-dev python-setuptools
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y git python-pip docker-ce
sudo usermod -aG docker $USER

git clone https://github.com/abcdabcd987/acm-compiler-judge.git
cd acm-compiler-judge/judge/docker-image
docker build -t acm-compiler-judge:latest -f production.Dockerfile .

cd ..
sudo -H pip install -r requirements.txt
cp settings.example.py settings.py
vim settings.py
./maintenance.py makedirs
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
