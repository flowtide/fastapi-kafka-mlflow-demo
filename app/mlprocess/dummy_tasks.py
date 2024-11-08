from confluent_kafka import Producer, KafkaException
import time
import mlflow
import logging
import time
import json
import os
from api_schema import TrainBody

logger = logging.getLogger(__name__)

def send_step_msg(producer: Producer, topic: str, step: str, modelId: str, text: str, exp_name: str, run_id: str=""):
    """
    Helper function to construct and send a Kafka message.
    """
    message = {
        "step": step,
        "modelId": modelId,
        "text": text,
        "expName": exp_name,
    }
    if run_id:
        message["run_id"] = run_id
    try:
        producer.produce(topic, value=json.dumps(message))
        producer.flush()
        logger.info(f"Sent message: {message}")
    except KafkaException as e:
        logger.error(f"Failed to send message to Kafka: {str(e)}")

def dummy_train_model(
    topic: str, producer: Producer, model_id: str, body: TrainBody,
    exp_name: str = "simulation_experiment"
):
    """
    Simulated training function with MLflow integration.
    Simulates logging parameters and metrics without actual model training.
    The simulation takes 10 seconds.

    :param model_name: The name of the model to simulate training for.
    :param exp_name: The name of the MLflow experiment.
    """
    model_name: str = "resnet50"
    send_step_msg(producer, topic, "preprocess", model_id, "TODO: preprocessing", exp_name)
    # MLflow experiment setup
    mlflow.set_experiment(exp_name)

    # If an active run exists, end it before starting a new one
    # if mlflow.active_run():
    #     mlflow.end_run()

    # Start a new MLflow run
    with mlflow.start_run() as run:
        run_id = run.info.run_id
        # Set a unique name for the run
        mlflow.set_tag("mlflow.runName", f"{exp_name}_{run_id}")
        text = f"Simulating training for model: {model_name}, Run ID: {run_id}"
        logger.info(text)
        send_step_msg(producer, topic, "train", model_id, text, exp_name, run_id)

        N_EPOCH = 10
        # Log parameters
        mlflow.log_param("model_name", model_name)
        mlflow.log_param("epochs", N_EPOCH)
        mlflow.log_param("batch_size", 32)

        # Simulate training process
        for epoch in range(N_EPOCH):
            time.sleep(1)  # Simulate one epoch taking 1 second
            train_loss = 0.1 * (N_EPOCH - epoch)  # Example: decreasing loss
            train_acc = 0.1 * (epoch + 1)    # Example: increasing accuracy

            # Log simulated metrics to MLflow
            mlflow.log_metrics({
                "train_loss": train_loss,
                "train_acc": train_acc,
            }, step=epoch)

            text = f"Epoch {epoch + 1}/10: Simulated Train Loss: {train_loss:.3f}, Train Acc: {train_acc:.3f}"
            logger.info(text)
            send_step_msg(producer, topic, "train", model_id, text, exp_name, run_id)

    try:
        # Simulate saving the model
        simulated_model_path = "README.md"
        full_path = os.path.join(os.getcwd(), simulated_model_path)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {full_path}")

        mlflow.log_artifact(full_path)  # Simulate logging an artifact
        print(f"Simulation complete for Run ID: {run_id}")
        text = f"Simulated model saved at {full_path}"
        send_step_msg(producer, topic, "end", model_id, text, exp_name, run_id)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        # Optionally send an error message or perform alternative actions
        text = f"Simulation failed: {e}"
        send_step_msg(producer, topic, "error", model_id, text, exp_name, run_id)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        text = f"Unexpected error: {e}"
        send_step_msg(producer, topic, "error", model_id, text, exp_name, run_id)
    
        return run_id
