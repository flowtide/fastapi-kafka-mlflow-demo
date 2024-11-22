# app/main.py
import os
import logging.config
from fastapi import FastAPI, BackgroundTasks, HTTPException
from confluent_kafka import Producer, KafkaException
from dotenv import load_dotenv

logging.config.fileConfig('logging.ini')
logger = logging.getLogger("root")

from mlprocess.tasks import train_task, predict
from api_schema import TrainRequest, TestRequest

# Load environment variables from .env file
load_dotenv()

# Get Kafka configurations from environment variables
KAFKA_ADDR = os.getenv('KAFKA_ADDR', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'test-topic')
APP_ENV = os.getenv('APP_ENV', 'development')
APP_PORT = int(os.getenv('APP_PORT', 3000))

# Create Kafka producer configuration
conf = {
    'bootstrap.servers': KAFKA_ADDR,
    #'debug': 'all'  # Enables detailed debugging
}

producer = Producer(conf)

app = FastAPI()

@app.post("/api/train")
async def train(request: TrainRequest, background_tasks: BackgroundTasks):
    logger.info(f"train: request={request}")
    try:
        background_tasks.add_task(train_task, KAFKA_TOPIC, producer, request)
    except Exception as e:
        logger.error(f"exception in train: {str(e)}")
        return {"message": f"Exception in train: {str(e)}"}

    return {"message": "ok"}

# /api/test 엔드포인트 정의
@app.post("/api/test")
async def test(request: TestRequest):
    try:
        test_input = request.test_input
        output = predict(test_input)
        return {"input": test_input, "output": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    if APP_ENV == 'development':
        uvicorn.run("main:app", host="0.0.0.0", port=APP_PORT, reload=True)
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=APP_PORT)
