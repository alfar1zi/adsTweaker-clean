import os
import uvicorn

print("BOOT: starting, PORT=", os.getenv("PORT"))
print("BOOT: has_key=", bool(os.getenv("DASHSCOPE_API_KEY")))

port = int(os.getenv("PORT", "8080"))
uvicorn.run("main:app", host="0.0.0.0", port=port)
