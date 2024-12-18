# FastAPI, Kafka and MLFlow demo

## Overall environment
- ip: 192.168.0.101
- minio(object storage) web: http://192.168.0.101:27441/, id=minio, password=miniostorage
- mlflow web: http://192.168.0.101:27442
- kafka api:
```
KAFKA_ADDR=localhost:15460
KAFKA_TOPIC=test-topic
# GROUP ID: 0
```

## Run Kafka

See [docker-compose/kafka](docker-compose/kafka)

## Run fastapi app
- Setup .env and edit it
```
cp env-sample .env
```
- Run
```
python app/main.py
```

## API test
- train
```
curl -X POST "http://localhost:15461/api/train" \
  -H "Content-Type: application/json"\
  -d '{
      "task_id": "task_12345",
      "hyperparameters": {
          "learning_rate": 0.001,
          "epochs": 10,
          "hidden_dim": 32
      },
      "dataset": [
          {"input": [1, 1], "output": [2]},
          {"input": [2, 3], "output": [5]},
          {"input": [3, 5], "output": [8]},
          {"input": [4, 7], "output": [11]},
          {"input": [5, 9], "output": [14]},
          {"input": [6, 11], "output": [17]},
          {"input": [7, 13], "output": [20]},
          {"input": [8, 15], "output": [23]},
          {"input": [9, 17], "output": [26]},
          {"input": [10, 19], "output": [29]},
          {"input": [11, 21], "output": [32]},
          {"input": [12, 23], "output": [35]},
          {"input": [13, 25], "output": [38]},
          {"input": [14, 27], "output": [41]},
          {"input": [15, 29], "output": [44]},
          {"input": [16, 31], "output": [47]},
          {"input": [17, 33], "output": [50]},
          {"input": [18, 35], "output": [53]},
          {"input": [19, 37], "output": [56]},
          {"input": [20, 39], "output": [59]}
      ],
      "train_valid_test_ratio": [0.7, 0.2, 0.1]
  }'
```

