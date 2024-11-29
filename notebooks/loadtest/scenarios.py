import nest_asyncio
nest_asyncio.apply()

async def run_notebook_tests():
    config = TestConfig(
        model_name="gpt-3.5-turbo",
        base_url="http://your-endpoint",
        api_key="your-key",
        client_type="openai",
        system_prompt="You are a helpful AI assistant.",
        verify_ssl=False,
        output_path="./test_results"
    )
    
    tester = LoadTester(config)
    results = {}
    
    # Basic test
    results['basic'] = await tester.run_latency_test(
        prompts=["What is artificial intelligence?"],
        concurrency=1
    )
    
    # Long prompt test
    long_prompt = "Explain the complete history of artificial intelligence, " * 50
    results['long_prompt'] = await tester.run_latency_test(
        prompts=[long_prompt],
        concurrency=1
    )
    
    # High temperature test
    config.temperature = 0.9
    tester = LoadTester(config)
    results['high_temp'] = await tester.run_latency_test(
        prompts=["Write a creative story about a robot."] * 5,
        concurrency=1
    )
    
    # Concurrent requests test
    config.temperature = 0.7
    tester = LoadTester(config)
    results['concurrent'] = await tester.run_latency_test(
        prompts=["Summarize the benefits of exercise."] * 10,
        concurrency=5
    )
    
    # Sustained load test
    results['sustained'] = await tester.run_sustained_load_test(
        prompt="What are the benefits of meditation?",
        requests_per_second=2,
        duration_seconds=30
    )
    
    return results

# Run tests
results = await run_notebook_tests()
print(json.dumps(results, indent=2))
