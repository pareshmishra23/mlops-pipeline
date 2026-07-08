import os
import logging
from typing import List, Dict, Any, Union
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from contextlib import asynccontextmanager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mlops-api")


# Request schema
class PredictionRequest(BaseModel):
    features: List[float] = Field(
        ...,
        description="List of numerical features for the model input.",
        examples=[[5.1, 3.5, 1.4, 0.2]],
    )


# Response schema
class PredictionResponse(BaseModel):
    prediction: Union[int, float, str] = Field(
        ..., description="The predicted class or regression value."
    )
    probability: float = Field(
        ..., description="The model's confidence or probability (0.0 to 1.0)."
    )
    model_version: str = Field(
        ..., description="Version of the model that served this request."
    )


# Mock Model implementation (to be replaced with actual model loading code,
# e.g., joblib.load, torch.load, or mlflow.pyfunc.load_model)
class ModelWrapper:
    def __init__(self):
        self.model_version = os.getenv("MODEL_VERSION", "mock-1.0.0")
        logger.info(f"Loading model version {self.model_version}...")
        # Simulate model load time or validation
        self.classes = ["setosa", "versicolor", "virginica"]

    def predict(self, features: List[float]) -> Dict[str, Any]:
        # Basic validation: ensure input has correct shape/length
        if len(features) != 4:
            raise ValueError(
                "Model expects exactly 4 features (e.g., Sepal/Petal lengths)."
            )

        # Mock prediction logic (e.g. sum features and modulo to select class)
        feature_sum = sum(features)
        prediction_idx = int(feature_sum) % len(self.classes)
        prediction = self.classes[prediction_idx]

        # Calculate a mock probability
        probability = min(1.0, max(0.0, (feature_sum % 10.0) / 10.0))

        return {
            "prediction": prediction,
            "probability": round(probability, 4),
            "model_version": self.model_version,
        }


# Instantiate model wrapper
model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    try:
        model = ModelWrapper()
        logger.info("Model loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise e
    yield
    logger.info("Cleaning up resources...")


# Initialize FastAPI App with lifespan
app = FastAPI(
    title="ML Model Inference API",
    description=(
        "Production-ready FastAPI endpoint for serving machine learning models."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", tags=["General"])
def read_root():
    return {
        "app": app.title,
        "status": "active",
        "model_version": model.model_version if model else "not_loaded",
    }


@app.get("/health", tags=["General"])
def health_check():
    """
    Liveness and readiness probe for orchestration platforms
    like Kubernetes, ECS, or Cloud Run.
    """
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded.",
        )
    return {"status": "healthy"}


@app.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Inference"],
)
def predict(request: PredictionRequest):
    """
    Submit features to get model prediction and confidence score.
    """
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is currently unavailable.",
        )

    try:
        result = model.predict(request.features)
        return PredictionResponse(**result)
    except ValueError as val_err:
        logger.warning(f"Validation error: {str(val_err)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as e:
        logger.error(f"Inference error occurred: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred during model inference.",
        )
