from pydantic import BaseModel
from typing import List, Dict


class TrainBodyMetadta(BaseModel):
    startTime: float
    endTime:float
    labelName:str
    labelId:str
    fileId:str
    cropId:str
    metadataId:str
    
class TrainBody(BaseModel):
    dataset: Dict[str,List[TrainBodyMetadta]]
    labels: Dict[str,str]