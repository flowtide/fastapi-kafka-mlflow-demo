# app/main.py
import os
import logging.config
from fastapi import FastAPI, BackgroundTasks
from confluent_kafka import Producer, KafkaException
from dotenv import load_dotenv
from pydantic import BaseModel
import json
from mlprocess.tasks import train_task
from mlprocess.dummy_tasks import dummy_train_model
from api_schema import TrainBody

# Load logging configuration
logging.config.fileConfig('logging.ini')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get Kafka configurations from environment variables
KAFKA_ADDR = os.getenv('KAFKA_ADDR', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'test-topic')
APP_ENV = os.getenv('APP_ENV', 'development')

# Create Kafka producer configuration
conf = {
    'bootstrap.servers': KAFKA_ADDR
}

producer = Producer(conf)

app = FastAPI()

@app.post('/api/v1/model/{modelId}/train')
async def train(modelId:str, body:TrainBody, background_tasks: BackgroundTasks):
    logger.info(f"train: model_id={modelId}, body={body}")
    try:
        msg = {
            "step": "start",
            "modelId": modelId,
            "text": f"train start"
        }
        producer.produce(KAFKA_TOPIC, value=json.dumps(msg))
        producer.flush()
    except KafkaException as e:
        return {"message": f"Failed to send message to Kafka: {str(e)}"}

    try:
        exp_name = 'test_1234'
        background_tasks.add_task(dummy_train_model, KAFKA_TOPIC, producer, modelId, body, exp_name)
    except Exception as e:
        logger.error(f"exception in train: {str(e)}")
        return {"message": f"Exception in train: {str(e)}"}

    return {"message": "ok"}

if __name__ == '__main__':
    import uvicorn
    if APP_ENV == 'development':
        uvicorn.run("main:app", host="0.0.0.0", port=28000, reload=True)
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=28000)
