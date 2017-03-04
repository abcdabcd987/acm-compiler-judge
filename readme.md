# Online Judge for Compiler Course @ ACM Honored Class, SJTU

## Setup Guide for the Core Server

```bash
sudo apt-get install -y git python-pip postgres
git clone https://github.com/abcdabcd987/acm-compiler-judge.git
cd acm-compiler-judge
sudo -H pip install -r requirements.txt
./maintenance.py initdb
./maintenance.py initdb <random_token>
./maintenance.py makedirs
cp settings.example.py settings.py
vim settings.py
```

## Setup Guide for Judge Server

```bash
sudo apt-get -y install apt-transport-https ca-certificates curl
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y git python-pip docker-ce
sudo usermod -aG docker $USER

git clone https://github.com/abcdabcd987/acm-compiler-judge.git
cd acm-compiler-judge/docker_image
docker build -t acm-compiler-judge:latest .

cd ..
cp settings.example.py settings.py
vim settings.py
```

## Run Core Server

```bash
# run core
./core/repo_watcher.py
./core/testrun_watcher.py

# run web
./core/core.py # debug run
```

## Run Judge Server

```bash
./judge/judge.py
```
