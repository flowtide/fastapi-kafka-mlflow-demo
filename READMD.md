# FastAPI, Kafka and MLFlow demo

## Run Kafka
```
docker run -d --name broker -p 9092:9092 apache/kafka:latest
# check server is ok
nc -zv localhost 9092
```
[kafka reference](https://hub.docker.com/r/apache/kafka)

## Run fastapi app
```
python app/main.py
```

## Test
```
curl -X POST "http://localhost:28000/api/v1/model/AAA/train" -H "Content-Type: application/json" -d '{
  "labels": {
    "6720600660c353de57e5d0a5": "강아지",
    "6720600660c353de57e5d0a6": "고양이"
  },
  "dataset": {
    "train": [
      {
        "startTime": 1.5697882362484008,
        "endTime": 3.569788236248401,
        "labelId": "6720600660c353de57e5d0a5",
        "labelName": "강아지",
        "metadataId": "672345848376997fdc1b6e28",
        "fileId": "672345848376997fdc1b6dfb",
        "cropId": "672432f6df39540243f068be"
      }
    ]
  }
```
