# Import asyncio for notebook compatibility
import nest_asyncio
nest_asyncio.apply()

async def run_notebook_tests():
    config = TestConfig(
        model_name="gpt-3.5-turbo",
        base_url="http://your-endpoint",
        api_key="your-key",
        client_type="openai",
        system_prompt="You are a helpful AI assistant."
    )
    
    tester = LoadTester(config)
    
    # Run individual tests
    results = {}
    
    # Test 1: Basic single request
    results['basic'] = await tester.run_latency_test(
        prompts=["What is artificial intelligence?"],
        concurrency=1
    )
    
    # Test 2: Long prompt
    long_prompt = "Explain the complete history of artificial intelligence, " * 50
    results['long_prompt'] = await tester.run_latency_test(
        prompts=[long_prompt],
        concurrency=1
    )
    
    # Additional tests...
    config.temperature = 0.9
    tester = LoadTester(config)
    results['high_temp'] = await tester.run_latency_test(
        prompts=["Write a creative story about a robot."] * 5,
        concurrency=1
    )
    
    return results

# Run tests and get results
results = await run_notebook_tests()
print(json.dumps(results, indent=2))
