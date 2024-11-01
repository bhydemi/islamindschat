from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from load_db import load_db

app = FastAPI()

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    db_query: Optional[str]
    db_response: Optional[List[str]]
    chat_history: List[str]

class CBFS:
    def __init__(self):
        self.chat_history = []
        self.loaded_file = "./The-Complete-Hadith.pdf"
        self.qa = load_db(self.loaded_file, "stuff", 4)
        self.db_query = ""
        self.db_response = []

    def call_load_db(self, file_path: str = None):
        if file_path:
            self.loaded_file = file_path
            self.qa = load_db(self.loaded_file, "stuff", 4)
        else:
            self.loaded_file = "./The-Complete-Hadith.pdf"
            self.qa = load_db(self.loaded_file, "stuff", 4)
        self.clear_history()

    def convchain(self, query: str):
        result = self.qa({"question": query, "chat_history": self.chat_history})
        self.chat_history.append((query, result["answer"]))
        self.db_query = result["generated_question"]
        self.db_response = result["source_documents"]
        return {
            "answer": result["answer"],
            "db_query": self.db_query,
            "db_response": self.db_response,
            "chat_history": self.chat_history
        }

    def clear_history(self):
        self.chat_history = []
        self.db_query = ""
        self.db_response = []

cbfs_instance = CBFS()

@app.post("/load_db/")
async def load_db_endpoint(file: Optional[UploadFile] = None):
    file_path = None
    if file:
        file_path = "temp.pdf"
        with open(file_path, "wb") as f:
            f.write(await file.read())
    cbfs_instance.call_load_db(file_path)
    return {"message": f"Loaded File: {cbfs_instance.loaded_file}"}

@app.post("/convchain/", response_model=ChatResponse)
async def convchain_endpoint(chat_request: ChatRequest):
    response = cbfs_instance.convchain(chat_request.query)
    return response

@app.post("/clear_history/")
async def clear_history_endpoint():
    cbfs_instance.clear_history()
    return {"message": "Chat history cleared"}

@app.get("/get_lquest/")
async def get_last_question():
    return {"db_query": cbfs_instance.db_query or "No DB accesses so far"}

@app.get("/get_sources/")
async def get_sources():
    if not cbfs_instance.db_response:
        return {"message": "No sources available"}
    return {"sources": cbfs_instance.db_response}

@app.get("/get_chats/")
async def get_chats():
    if not cbfs_instance.chat_history:
        return {"message": "No chat history yet"}
    return {"chat_history": cbfs_instance.chat_history}