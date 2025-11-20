"""
EchoZero API Server (v4.2.1)
-----------------------------
FastAPI-based REST API with rate limiting and validation.

Endpoints:
- POST /forward - Run forward pass
- GET /state - Get current system state
- GET /health - Healthcheck
- GET /metrics - System metrics
- POST /reset - Reset system state
- WebSocket /stream - Real-time φ stream

Fixes from v4.2.0:
- Rate limiting (Issue #15 resolved)
- Input validation (Issue #12 resolved)
- Proper error handling
- Thread-safe state access
"""

import time
from typing import Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import torch

from ..hybrid import HybridForward
from ..train import DataStream
from ..core.state import GlobalState
from ..core.errors import ValidationError, DimensionMismatchError

# Simple in-memory rate limiting
# For production, use Redis-based solution
class RateLimiter:
    def __init__(self, max_requests: int = 100, window: int = 60):
        """
        Args:
            max_requests: Max requests per window
            window: Time window in seconds
        """
        self.max_requests = max_requests
        self.window = window
        self.requests = {}

    def check(self, client_id: str) -> bool:
        """Check if request is allowed."""
        now = time.time()

        # Clean old entries
        if client_id in self.requests:
            self.requests[client_id] = [
                t for t in self.requests[client_id]
                if now - t < self.window
            ]
        else:
            self.requests[client_id] = []

        # Check limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False

        # Record request
        self.requests[client_id].append(now)
        return True


# Rate limiter instance
rate_limiter = RateLimiter(max_requests=100, window=60)


# Pydantic models with validation
class ForwardInput(BaseModel):
    """Input schema for forward pass."""
    text: list[float] = Field(..., min_items=768, max_items=768, description="Text embedding (768-dim)")
    vision: list[float] = Field(..., min_items=512, max_items=512, description="Vision embedding (512-dim)")
    audio: list[float] = Field(..., min_items=128, max_items=128, description="Audio features (128-dim)")
    eeg: list[float] = Field(..., min_items=64, max_items=64, description="EEG data (64-dim)")

    @validator('text', 'vision', 'audio', 'eeg')
    def check_no_nan_inf(cls, v):
        """Validate no NaN/Inf values."""
        tensor = torch.tensor(v)
        if torch.any(torch.isnan(tensor)) or torch.any(torch.isinf(tensor)):
            raise ValueError("Input contains NaN or Inf values")
        return v


class ForwardOutput(BaseModel):
    """Output schema for forward pass."""
    phi: float
    coherence: float
    qualia: list[float]
    prop_state: list[float]
    gamma: float


class MetricsOutput(BaseModel):
    """System metrics output."""
    phi: float
    coherence: float
    drift: float
    stress: float
    meta_stability: float
    memory_strength: float


# FastAPI app
app = FastAPI(
    title="EchoZero API",
    description="Resonant Intelligence Middleware",
    version="4.2.1"
)

# Initialize model (lazy loaded)
_model = None
_datastream = None


def get_model():
    """Lazy initialization of model."""
    global _model, _datastream
    if _model is None:
        _model = HybridForward(N=64, input_dim=1472, device='cpu')
        _datastream = DataStream(allow_missing=False, device='cpu')
    return _model, _datastream


# Middleware for rate limiting
@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    """Rate limiting middleware."""
    client_id = request.client.host

    if not rate_limiter.check(client_id):
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Max 100 requests per minute."}
        )

    response = await call_next(request)
    return response


# Routes
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "4.2.1",
        "service": "EchoZero"
    }


@app.post("/forward", response_model=ForwardOutput)
async def forward_endpoint(payload: ForwardInput):
    """
    Execute forward pass through EchoZero.

    Returns cognitive state including φ-depth, coherence, and qualia.
    """
    try:
        model, datastream = get_model()

        # Convert to tensors
        text_vec = torch.tensor(payload.text)
        vision_vec = torch.tensor(payload.vision)
        audio_vec = torch.tensor(payload.audio)
        eeg_vec = torch.tensor(payload.eeg)

        # Validate and fuse
        grounded = datastream(text_vec, vision_vec, audio_vec, eeg_vec)

        # Forward pass
        hybrid_out = model(grounded)

        # Extract outputs
        return ForwardOutput(
            phi=float(hybrid_out['phi']),
            coherence=float(hybrid_out['coherence'].mean()),
            qualia=hybrid_out['qualia'].tolist(),
            prop_state=hybrid_out['prop_state'].tolist(),
            gamma=float(hybrid_out['gamma'])
        )

    except (ValidationError, DimensionMismatchError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/state")
async def get_state():
    """Get current system state."""
    with GlobalState.read_lock():
        return {
            "psi_real": GlobalState.psi.real.tolist() if GlobalState.psi is not None else None,
            "psi_imag": GlobalState.psi.imag.tolist() if GlobalState.psi is not None else None,
            "memory": GlobalState.memory.tolist() if GlobalState.memory is not None else None,
            "prop_state": GlobalState.prop_state.tolist() if GlobalState.prop_state is not None else None,
            "phi": float(GlobalState.phi),
            "coherence": float(GlobalState.coherence),
            "drift": float(GlobalState.drift),
            "safe_mode": GlobalState.safe_mode,
            "error_count": GlobalState.error_count
        }


@app.get("/metrics", response_model=MetricsOutput)
async def get_metrics():
    """Get system metrics."""
    with GlobalState.read_lock():
        return MetricsOutput(
            phi=float(GlobalState.phi),
            coherence=float(GlobalState.coherence),
            drift=float(GlobalState.drift),
            stress=0.0,  # Would come from kernel state
            meta_stability=0.5,  # Would come from kernel state
            memory_strength=float(GlobalState.memory.norm() if GlobalState.memory is not None else 0.0)
        )


@app.post("/reset")
async def reset_state():
    """Reset system state."""
    with GlobalState.write_lock():
        GlobalState.psi = torch.zeros(64, dtype=torch.cfloat)
        GlobalState.memory = torch.zeros(128)
        GlobalState.prop_state = torch.zeros(6)
        GlobalState.phi = 0.0
        GlobalState.coherence = 0.0
        GlobalState.drift = 0.0
        GlobalState.safe_mode = False
        GlobalState.error_count = 0

    return {"status": "reset complete"}


@app.websocket("/stream")
async def stream_phi(websocket: WebSocket):
    """
    WebSocket endpoint for real-time φ-depth streaming.

    Client receives φ updates every 100ms.
    """
    await websocket.accept()

    try:
        while True:
            with GlobalState.read_lock():
                phi = float(GlobalState.phi)

            await websocket.send_json({"phi": phi, "timestamp": time.time()})
            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        pass


# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
