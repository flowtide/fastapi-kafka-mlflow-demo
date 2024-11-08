from confluent_kafka import Producer, KafkaException
import logging
import time
import json
from api_schema import TrainBody

logger = logging.getLogger(__name__)

def send_step_msg(producer: Producer, topic: str, step: str, modelId: str, text: str):
    """
    Helper function to construct and send a Kafka message.
    """
    message = {
        "step": step,
        "modelId": modelId,
        "text": text
    }
    try:
        producer.produce(topic, value=json.dumps(message))
        producer.flush()
        logger.info(f"Sent message: {message}")
    except KafkaException as e:
        logger.error(f"Failed to send message to Kafka: {str(e)}")

def train_task(topic: str, producer: Producer, modelId: str, body: TrainBody):
    send_step_msg(producer, topic, "preprocess", modelId, "train start")

    # Simulated training loop
    for i in range(10):
        time.sleep(1)
        send_step_msg(producer, topic, "train", modelId, f"train progress {i + 1}/10")
