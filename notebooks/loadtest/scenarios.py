import asyncio
from load_tester import TestConfig, LoadTester

async def run_test_suite():
    config = TestConfig(
        model_name="gpt-3.5-turbo",
        base_url="http://your-endpoint",
        api_key="your-key",
        client_type="openai",
        system_prompt="You are a helpful AI assistant."
    )
    
    tester = LoadTester(config)
    
    # Test 1: Basic single request
    print("\n=== Test 1: Basic Single Request ===")
    results = await tester.run_latency_test(
        prompts=["What is artificial intelligence?"],
        concurrency=1
    )
    print(json.dumps(results, indent=2))
    
    # Test 2: Long prompt test
    print("\n=== Test 2: Long Prompt Test ===")
    long_prompt = "Explain the complete history of artificial intelligence, " * 50
    results = await tester.run_latency_test(
        prompts=[long_prompt],
        concurrency=1
    )
    print(json.dumps(results, indent=2))
    
    # Test 3: High temperature creative tasks
    print("\n=== Test 3: High Temperature Test ===")
    config.temperature = 0.9
    tester = LoadTester(config)
    results = await tester.run_latency_test(
        prompts=["Write a creative story about a robot."] * 5,
        concurrency=1
    )
    print(json.dumps(results, indent=2))
    
    # Test 4: Concurrent requests
    print("\n=== Test 4: Concurrent Requests Test ===")
    config.temperature = 0.7  # Reset temperature
    tester = LoadTester(config)
    results = await tester.run_latency_test(
        prompts=["Summarize the benefits of exercise."] * 10,
        concurrency=5
    )
    print(json.dumps(results, indent=2))
    
    # Test 5: Sustained load
    print("\n=== Test 5: Sustained Load Test ===")
    results = await tester.run_sustained_load_test(
        prompt="What are the benefits of meditation?",
        requests_per_second=2,
        duration_seconds=30
    )
    print(json.dumps(results, indent=2))
    
    # Test 6: Variable length prompts with concurrency
    print("\n=== Test 6: Variable Length with Concurrency ===")
    base_prompt = "Explain quantum computing"
    variable_prompts = tester.generate_variable_length_prompts(
        base_prompt=base_prompt,
        n_prompts=15,
        min_length=100,
        max_length=2000
    )
    results = await tester.run_latency_test(
        prompts=variable_prompts,
        concurrency=3
    )
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(run_test_suite())
