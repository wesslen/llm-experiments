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
import httpx
import os
from datetime import datetime

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
    verify_ssl: bool = True
    output_path: Optional[str] = None
    
class LoadTester:
    def __init__(self, config: TestConfig):
        self.config = config
        self.setup_client()
        self.results = []
        if self.config.output_path:
            os.makedirs(self.config.output_path, exist_ok=True)
        
    def setup_client(self):
        if self.config.client_type == "openai":
            openai.api_key = self.config.api_key
            openai.base_url = self.config.base_url
            openai.http_client = httpx.Client(verify=self.config.verify_ssl)
        elif self.config.client_type == "langchain":
            self.client = ChatOpenAI(
                model_name=self.config.model_name,
                openai_api_key=self.config.api_key,
                base_url=self.config.base_url,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                max_tokens=self.config.max_tokens,
                client=httpx.Client(verify=self.config.verify_ssl)
            )

    def count_tokens(self, text: str) -> int:
        # Simple approximation: 4 chars ~ 1 token
        return len(text) // 4

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
                        },
                        ssl=self.config.verify_ssl
                    ) as response:
                        response_json = await response.json()
                        if 'error' in response_json:
                            raise Exception(response_json['error'])
                        completion = response_json['choices'][0]['message']['content']
                        
            elif self.config.client_type == "openai":
                response = await openai.chat.completions.create(
                    model=self.config.model_name,
                    messages=[
                        {"role": "system", "content": self.config.system_prompt or ""},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    max_tokens=self.config.max_tokens
                )
                completion = response.choices[0].message.content
                
            elif self.config.client_type == "langchain":
                messages = []
                if self.config.system_prompt:
                    messages.append(SystemMessage(content=self.config.system_prompt))
                messages.append(HumanMessage(content=prompt))
                response = await self.client.agenerate([messages])
                completion = response.generations[0][0].text
                
            latency = time.time() - start_time
            output_tokens = self.count_tokens(completion)
            throughput = output_tokens / latency if latency > 0 else 0
            
            return {
                "success": True,
                "latency": latency,
                "prompt_length": len(prompt),
                "output_tokens": output_tokens,
                "throughput": throughput,
                "completion": completion
            }
            
        except Exception as e:
            logging.error(f"Request failed: {str(e)}\nPrompt: {prompt}")
            return {
                "success": False,
                "error": str(e),
                "prompt_length": len(prompt),
                "output_tokens": 0,
                "throughput": 0
            }

    def save_results(self, results: dict, test_name: str):
        if self.config.output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{test_name}_{timestamp}.json"
            filepath = os.path.join(self.config.output_path, filename)
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2)

    def analyze_results(self, results: List[dict]) -> dict:
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        if not successful_requests:
            return {"error": "All requests failed"}
            
        latencies = [r["latency"] for r in successful_requests]
        throughputs = [r["throughput"] for r in successful_requests]
        output_tokens = [r["output_tokens"] for r in successful_requests]
        
        analysis = {
            "total_requests": len(results),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "latency": {
                "avg": statistics.mean(latencies),
                "p50": np.percentile(latencies, 50),
                "p95": np.percentile(latencies, 95),
                "p99": np.percentile(latencies, 99),
                "min": min(latencies),
                "max": max(latencies)
            },
            "throughput": {
                "avg": statistics.mean(throughputs),
                "p50": np.percentile(throughputs, 50),
                "p95": np.percentile(throughputs, 95),
                "p99": np.percentile(throughputs, 99),
                "min": min(throughputs),
                "max": max(throughputs)
            },
            "output_tokens": {
                "total": sum(output_tokens),
                "avg": statistics.mean(output_tokens),
                "p50": np.percentile(output_tokens, 50),
                "p95": np.percentile(output_tokens, 95),
                "p99": np.percentile(output_tokens, 99)
            }
        }
        
        return analysis

    async def run_latency_test(self, prompts: List[str], concurrency: int = 1):
        async def _batch_requests(batch: List[str]):
            tasks = [self._make_request(prompt) for prompt in batch]
            return await asyncio.gather(*tasks)
            
        results = []
        for i in range(0, len(prompts), concurrency):
            batch = prompts[i:i + concurrency]
            batch_results = await _batch_requests(batch)
            results.extend(batch_results)
            
        analysis = self.analyze_results(results)
        self.save_results(analysis, "latency_test")
        return analysis
    
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
            
            elapsed = time.time() - before_request
            wait_time = max(0, (1 / requests_per_second) - elapsed)
            await asyncio.sleep(wait_time)
            
        analysis = self.analyze_results(results)
        self.save_results(analysis, "sustained_test")
        return analysis
    
    def generate_variable_length_prompts(self, 
                                       base_prompt: str, 
                                       n_prompts: int,
                                       min_length: int = 100,
                                       max_length: int = 1000) -> List[str]:
        lengths = np.linspace(min_length, max_length, n_prompts, dtype=int)
        prompts = []
        
        for length in lengths:
            padding_length = max(0, length - len(base_prompt))
            padding = "X" * padding_length
            prompts.append(base_prompt + padding)
            
        return prompts
