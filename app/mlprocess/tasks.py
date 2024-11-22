from confluent_kafka import Producer, KafkaException
import logging
import traceback
import json
from api_schema import TrainRequest
import torch
import torch.nn as nn
import torch.optim as optim
import random
import mlflow
import mlflow.pytorch

logger = logging.getLogger("tasks")
model = None  # Define the model globally for accessibility across functions

class ArithmeticNN(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super(ArithmeticNN, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, output_dim)
        logger.info(f"Model Architecture: input_dim={input_dim}, hidden_dim={hidden_dim}, output_dim={output_dim}")
    
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x

    def print_parameters(self):
        logger.info(f" -- Model: {self._get_name()}")
        for name, param in self.named_parameters():
            logger.info(f"  Parameter {name}: {param.size()}")

def train_model(model, train_data, valid_data, hyperparameters, producer, topic, task_id, run_id):
    logger.info(f"Training with hyperparameters: {hyperparameters}")
    optimizer = optim.Adam(model.parameters(), lr=hyperparameters.get("learning_rate", 0.001))
    criterion = nn.MSELoss()
    model.print_parameters()
    model.train()
    mlflow.log_params(hyperparameters)

    for epoch in range(int(hyperparameters.get("epochs", 10))):
        train_loss = 0
        valid_loss = 0
        correct_predictions = 0

        # Training phase
        model.train()
        for data in train_data:
            inputs = torch.tensor(data["input"], dtype=torch.float32).unsqueeze(0)
            labels = torch.tensor(data["output"], dtype=torch.float32).unsqueeze(1)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

            # Calculate training accuracy
            predicted = torch.round(outputs)
            if predicted.item() == labels.item():
                correct_predictions += 1

        train_loss /= len(train_data)
        train_accuracy = correct_predictions / len(train_data)

        # Validation phase
        model.eval()
        with torch.no_grad():
            for data in valid_data:
                inputs = torch.tensor(data["input"], dtype=torch.float32).unsqueeze(0)
                labels = torch.tensor(data["output"], dtype=torch.float32).unsqueeze(1)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                valid_loss += loss.item()
        valid_loss /= len(valid_data)

        logger.info(f"Epoch {epoch+1}, Train Loss: {train_loss:.5f}, Validation Loss: {valid_loss:.5f}, Train Accuracy: {train_accuracy:.5f}")
        # Log metrics to MLflow
        mlflow.log_metric("train_loss", train_loss, step=epoch+1)
        mlflow.log_metric("valid_loss", valid_loss, step=epoch+1)
        mlflow.log_metric("train_accuracy", train_accuracy, step=epoch+1)

        # Send training accuracy to Kafka every 5 epochs
        if (epoch + 1) % 5 == 0:
            send_step_msg(
                producer=producer,
                topic=topic,
                task_id=task_id,
                epoch=epoch+1,
                run_id=run_id,
                text=f"train_accuracy: {round(train_accuracy, 5)}, train_loss: {round(train_loss, 5)}, valid_loss: {round(valid_loss, 5)}"
            )

    logger.info(f"log_model...")
    mlflow.pytorch.log_model(model, "model")

    return round(train_loss, 5), round(valid_loss, 5)

def split_dataset(dataset, ratios):
    random.shuffle(dataset)
    train_size = int(len(dataset) * ratios[0])
    valid_size = int(len(dataset) * ratios[1])
    train_data = dataset[:train_size]
    valid_data = dataset[train_size:train_size + valid_size]
    test_data = dataset[train_size + valid_size:]
    return train_data, valid_data, test_data

def evaluate_model(model, test_data):
    model.eval()
    correct = 0
    total = len(test_data)
    with torch.no_grad():
        for data in test_data:
            inputs = torch.tensor(data["input"], dtype=torch.float32).unsqueeze(0)
            labels = torch.tensor(data["output"], dtype=torch.float32).unsqueeze(1)
            outputs = model(inputs)
            predicted = torch.round(outputs)
            
            is_correct = (predicted.item() == labels.item())
            logger.info(f"Test: input={data['input']}, predicted={predicted.item()}, labels={labels.item()}, is_correct={is_correct}")
            
            if is_correct:
                correct += 1

    accuracy = correct / total if total > 0 else 0
    return accuracy

def train_task(topic: str, producer: Producer, request: TrainRequest):
    global model
    try:
        task_id = request.task_id
        hyperparameters = request.hyperparameters
        dataset = request.dataset
        ratios = request.train_valid_test_ratio

        train_data, valid_data, test_data = split_dataset(dataset, ratios)

        input_dim = len(dataset[0]["input"])
        hidden_dim = int(hyperparameters.get("hidden_dim", 32))
        output_dim = 1
        model = ArithmeticNN(input_dim, hidden_dim, output_dim)

        # Ensure no active run before starting a new one
        if mlflow.active_run():
            logger.warning(f"Ending existing MLflow run with ID: {mlflow.active_run().info.run_id}")
            mlflow.end_run()

        # Start a new MLflow run
        with mlflow.start_run() as run:
            experiment = model._get_name()
            mlflow.set_experiment(experiment) # set experiment with model name
            mlflow.set_tag("mlflow.source.name", __name__)
            logger.info(f"Started MLflow: experiment={experiment},run_name={run.info.run_name},run_id={run.info.run_id}")
            final_train_loss, final_valid_loss = train_model(
                model, train_data, valid_data, hyperparameters, producer, topic, task_id, run.info.run_id
            )
            accuracy = evaluate_model(model, test_data)
            logging.info(f"Test: {test_data} -> accuracy={accuracy}")
            mlflow.log_metric("test_accuracy", accuracy)
            # Send final training summary to Kafka
            send_training_summary(
                producer=producer,
                topic=topic,
                run_id=run.info.run_id,
                train_loss=final_train_loss,
                valid_loss=final_valid_loss,
                accuracy=accuracy,
                request=request
            )
    except Exception as e:
        logger.error(f"Exception while training: {e}")
        logger.error(traceback.format_exc())
        send_error_message(
            producer=producer,
            topic=topic,
            task_id=request.task_id,
            text=str(e),
        )
    finally:
        if mlflow.active_run():
            logger.info(f"Ending MLflow run with ID: {run.info.run_id}")
            mlflow.end_run()

def send_step_msg(producer: Producer, topic: str, task_id: str, epoch: int, run_id: str, text: str):
    """
    Helper function to construct and send a Kafka message.
    """
    message = {
        "task_id": task_id,
        "epoch": epoch,
        "run_id": run_id,
        "status": "train",
        "text": text
    }
    try:
        producer.produce(topic, value=json.dumps(message))
        producer.flush()
        logger.info(f"Sent message: {message}")
    except KafkaException as e:
        logger.error(f"Failed to send message to Kafka: {str(e)}")


def send_training_summary(producer: Producer, topic: str, run_id: str, train_loss: float, valid_loss: float, accuracy: float, request):
    message = {
        "run_id": run_id,
        "summary": {
            "train_loss": train_loss,
            "valid_loss": valid_loss,
            "accuracy": accuracy
        },
        "status": "done",
        "request": request.dict()
    }
    try:
        producer.produce(topic, value=json.dumps(message))
        producer.flush()
        logger.info(f"Sent training summary: {message}")
    except KafkaException as e:
        logger.error(f"Failed to send training summary to Kafka: {str(e)}")

def send_error_message(producer: Producer, topic: str, task_id: str, text: str):
    """
    Sends an error message to Kafka in case of exceptions during training.
    """
    message = {
        "task_id": task_id,
        "text": text,
        "status": "error"
    }
    try:
        producer.produce(topic, value=json.dumps(message))
        producer.flush()
        logger.error(f"Sent error message: {message}")
    except KafkaException as e:
        logger.error(f"Failed to send error message to Kafka: {str(e)}")

def predict(test_input):
    global model
    inputs = torch.tensor(test_input, dtype=torch.float32).unsqueeze(0)
    model.eval()
    with torch.no_grad():
        output = model(inputs)
    logger.info(f"predict: {inputs} => {output.item()}")
    return output.item()
