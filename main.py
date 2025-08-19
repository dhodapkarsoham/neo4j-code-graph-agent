import uvicorn

if __name__ == "__main__":
    # Use reload for auto-restart on code changes (like nodemon)
    uvicorn.run("src.web_ui:app", host="127.0.0.1", port=8000, reload=True, reload_dirs=["src"]) 
