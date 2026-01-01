import os
from typing import List, Dict
from mem0 import MemoryClient
import uuid

class MemoryManager:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.client = MemoryClient(api_key=os.getenv("MEM0_API_KEY"))
    
    def add_memory(self, user_message: str, ai_response: str):
        """Store conversation in memory"""
        try:
            # Create messages list as per Mem0 documentation
            messages = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": ai_response}
            ]
            
            # Add to memory (let Mem0 infer what to remember)
            self.client.add(
                messages=messages,
                user_id=self.user_id,
                metadata={"type": "conversation"}
            )
        except Exception as e:
            print(f"Warning: Failed to add memory: {e}")
    
    def get_relevant_memories(self, current_message: str):
        try:
            memories = self.client.search(
            query=current_message,
            filters={
                "AND": [
                    {"user_id": self.user_id},
                    {"metadata": {"type": "fact"}}
                ]
            },
            limit=5
        )

            
            results = []
            for mem in memories.get("results", []):
                text = mem.get("memory") or mem.get("text")
                if text:
                    results.append(text)

            return results

        except Exception as e:
            # Never break chat for memory failure
            print(f"Memory search skipped: {e}")
            return []


    
    def store_user_fact(self, fact: str):
        self.client.add(
            messages=[
                {"role": "user", "content": fact}
            ],
            user_id=self.user_id,
            metadata={"type": "fact"}
        )
    def delete_user_memories(self):
        """Delete all memories for the user"""
        try:
            self.client.delete_all(
                user_id=self.user_id
            )
        except Exception as e:
            print(f"Warning: Failed to delete memories: {e}")
