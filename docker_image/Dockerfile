FROM ubuntu:16.04

## debug build
RUN sed -i 's/archive.ubuntu.com/ftp.sjtu.edu.cn/g' /etc/apt/sources.list
RUN apt-get update && \
    apt-get install -y build-essential openjdk-8-jdk time

## production build
# RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections
# RUN add-apt-repository -y ppa:webupd8team/java
# RUN apt-get update
# RUN apt-get install -y oracle-java8-installer build-essential time
# RUN rm -rf /var/lib/apt/lists/*
# RUN rm -rf /var/cache/oracle-jdk8-install
# ENV JAVA_HOME /usr/lib/jvm/java-8-oracle

CMD ["bash"]

