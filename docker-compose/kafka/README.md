# Kafka Installation

It seems better to use `confluentinc/cp-kafka` than `apache/kafka`.

## Run Kafka docker
```
docker-compose up -d
# check server is ok
nc -zv localhost 15460
```
[kafka reference](https://hub.docker.com/r/apache/kafka)

## Setup Kafka tools

```
wget https://downloads.apache.org/kafka/3.9.0/kafka_2.13-3.9.0.tgz
tar xvf kafka_2.13-3.9.0.tgz
sudo mkdir -p /opt/kafka
sudo mv kafka_2.13-3.9.0 /opt/kafka/bin
sudo apt install default-jre
PATH=$PATH:/opt/kafka/bin
```

## Kafka Tools Usage
- produce message
```
kafka-console-producer.sh --bootstrap-server localhost:9092 --topic test-topic
```
- consume message
```
kafka-console-consumer.sh --bootstrap-server localhost:15460 -topic test-topic --from-beginning
```
