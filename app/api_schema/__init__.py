from pydantic import BaseModel
from typing import List, Dict

class TrainRequest(BaseModel):
    task_id: str
    hyperparameters: Dict[str, float]  # 학습률, 은닉층 크기 등
    dataset: List[Dict[str, List[int]]]  # [{"input": [x1, x2], "output": y}, ...]
    train_valid_test_ratio: List[float]  # [train_ratio, valid_ratio, test_ratio]

class TestRequest(BaseModel):
    test_input: List[int]
