import os
import uvicorn

if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host=host, port=port, log_level="info")
