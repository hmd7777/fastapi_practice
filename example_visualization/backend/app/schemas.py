from pydantic import BaseModel

class IrisOut(BaseModel):
    id: int
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float
    species: str

    class Config:
        from_attributes = True

