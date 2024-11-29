import asyncio
import time
import aiohttp
import statistics
from dataclasses import dataclass
from typing import List, Optional, Literal, Union
import numpy as np
import json
import logging
from concurrent.futures import ThreadPoolExecutor
import openai
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

@dataclass
class TestConfig:
    model_name: str
    base_url: str
    api_key: str
    client_type: Literal["requests", "openai", "langchain"]
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: int = 1000
    
class LoadTester:
    def __init__(self, config: TestConfig):
        self.config = config
        self.setup_client()
        self.results = []
        
    def setup_client(self):
        if self.config.client_type == "openai":
            openai.api_key = self.config.api_key
            openai.base_url = self.config.base_url
        elif self.config.client_type == "langchain":
            self.client = ChatOpenAI(
                model_name=self.config.model_name,
                openai_api_key=self.config.api_key,
                base_url=self.config.base_url,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                max_tokens=self.config.max_tokens
            )

    async def _make_request(self, prompt: str) -> dict:
        start_time = time.time()
        try:
            if self.config.client_type == "requests":
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.config.base_url}/v1/chat/completions",
                        headers={"Authorization": f"Bearer {self.config.api_key}"},
                        json={
                            "model": self.config.model_name,
                            "messages": [
                                {"role": "system", "content": self.config.system_prompt or ""},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": self.config.temperature,
                            "top_p": self.config.top_p,
                            "max_tokens": self.config.max_tokens
                        }
                    ) as response:
                        result = await response.json()
                        
            elif self.config.client_type == "openai":
                result = await openai.chat.completions.create(
                    model=self.config.model_name,
                    messages=[
                        {"role": "system", "content": self.config.system_prompt or ""},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    max_tokens=self.config.max_tokens
                )
                
            elif self.config.client_type == "langchain":
                messages = []
                if self.config.system_prompt:
                    messages.append(SystemMessage(content=self.config.system_prompt))
                messages.append(HumanMessage(content=prompt))
                result = await self.client.agenerate([messages])
                
            latency = time.time() - start_time
            return {"success": True, "latency": latency, "prompt_length": len(prompt)}
            
        except Exception as e:
            logging.error(f"Request failed: {str(e)}")
            return {"success": False, "error": str(e), "prompt_length": len(prompt)}

    async def run_latency_test(self, prompts: List[str], concurrency: int = 1):
        async def _batch_requests(batch: List[str]):
            tasks = [self._make_request(prompt) for prompt in batch]
            return await asyncio.gather(*tasks)
            
        results = []
        for i in range(0, len(prompts), concurrency):
            batch = prompts[i:i + concurrency]
            batch_results = await _batch_requests(batch)
            results.extend(batch_results)
            
        return self.analyze_results(results)
    
    async def run_sustained_load_test(self, 
                                    prompt: str, 
                                    requests_per_second: float, 
                                    duration_seconds: int):
        start_time = time.time()
        results = []
        
        while time.time() - start_time < duration_seconds:
            before_request = time.time()
            result = await self._make_request(prompt)
            results.append(result)
            
            # Wait to maintain desired RPS
            elapsed = time.time() - before_request
            wait_time = max(0, (1 / requests_per_second) - elapsed)
            await asyncio.sleep(wait_time)
            
        return self.analyze_results(results)
    
    def analyze_results(self, results: List[dict]) -> dict:
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        if not successful_requests:
            return {"error": "All requests failed"}
            
        latencies = [r["latency"] for r in successful_requests]
        
        return {
            "total_requests": len(results),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "avg_latency": statistics.mean(latencies),
            "p50_latency": np.percentile(latencies, 50),
            "p95_latency": np.percentile(latencies, 95),
            "p99_latency": np.percentile(latencies, 99),
            "min_latency": min(latencies),
            "max_latency": max(latencies)
        }

    def generate_variable_length_prompts(self, 
                                       base_prompt: str, 
                                       n_prompts: int,
                                       min_length: int = 100,
                                       max_length: int = 1000) -> List[str]:
        lengths = np.linspace(min_length, max_length, n_prompts, dtype=int)
        prompts = []
        
        for length in lengths:
            # Pad the base prompt with random text to reach desired length
            padding_length = max(0, length - len(base_prompt))
            padding = "X" * padding_length
            prompts.append(base_prompt + padding)
            
        return prompts
