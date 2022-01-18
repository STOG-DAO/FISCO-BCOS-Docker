FROM ubuntu:20.04
  
ENV USER root

ENV PATH /root/.local/bin/:$PATH

RUN mkdir /fisco

WORKDIR /fisco

RUN apt-get update && \
    apt install -y openssl curl

RUN cd /fisco && \
    curl -#LO https://github.com/FISCO-BCOS/FISCO-BCOS/releases/download/v2.8.0/build_chain.sh && \
    chmod u+x build_chain.sh

#EXPOSE 30300 20200 8545

CMD ["bash"]