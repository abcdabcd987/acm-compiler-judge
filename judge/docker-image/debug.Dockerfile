FROM ubuntu:16.04

# debug build
RUN sed -i 's/archive.ubuntu.com/ftp.sjtu.edu.cn/g' /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y build-essential openjdk-8-jdk time nasm unzip

CMD ["bash"]

