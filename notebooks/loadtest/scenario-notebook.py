import nest_asyncio
import asyncio
import json
import numpy as np
nest_asyncio.apply()

async def run_optimized_tests():
    base_config = TestConfig(
        model_name="your-model",
        base_url="your-endpoint",
        api_key="your-key",
        client_type="openai",
        verify_ssl=False
    )
    
    results = {}
    
    # 1. Baseline Test
    tester = LoadTester(base_config)
    results['baseline'] = await tester.run_latency_test(
        prompts=["Explain what is artificial intelligence in one sentence."],
        concurrency=1
    )
    
    # 2. Length Impact Test
    base_prompt = "Explain the concept of machine learning"
    variable_prompts = tester.generate_variable_length_prompts(
        base_prompt=base_prompt,
        n_prompts=5,
        min_length=100,
        max_length=4000
    )
    results['length_impact'] = await tester.run_latency_test(
        prompts=variable_prompts,
        concurrency=1
    )
    
    # 3. Temperature Variation Test
    temps = [0.1, 0.5, 0.9]
    temp_results = {}
    for temp in temps:
        base_config.temperature = temp
        tester = LoadTester(base_config)
        temp_results[str(temp)] = await tester.run_latency_test(
            prompts=["Write a creative story about AI"] * 3,
            concurrency=1
        )
    results['temperature_variation'] = temp_results
    
    # 4. Basic Concurrent Test
    base_config.temperature = 0.7  # Reset temperature
    tester = LoadTester(base_config)
    results['concurrent_basic'] = await tester.run_latency_test(
        prompts=["What are the benefits of AI?"] * 5,
        concurrency=5
    )
    
    # 5. Sustained Light Load
    results['sustained_light'] = await tester.run_sustained_load_test(
        prompt="Explain quantum computing briefly.",
        requests_per_second=1,
        duration_seconds=30
    )
    
    # 6. Sustained Medium Load
    results['sustained_medium'] = await tester.run_sustained_load_test(
        prompt="Explain quantum computing briefly.",
        requests_per_second=3,
        duration_seconds=30
    )
    
    # 7. Burst Test
    results['burst'] = await tester.run_latency_test(
        prompts=["Summarize the benefits of AI."] * 10,
        concurrency=10
    )
    
    # 8. Mixed Length Concurrent
    mixed_prompts = tester.generate_variable_length_prompts(
        base_prompt="Explain machine learning",
        n_prompts=10,
        min_length=100,
        max_length=2000
    )
    results['mixed_length_concurrent'] = await tester.run_latency_test(
        prompts=mixed_prompts,
        concurrency=5
    )
    
    # 9. Progressive Concurrency
    prog_results = {}
    for concurrency in [1, 5, 10, 15]:
        prog_results[f"concurrency_{concurrency}"] = await tester.run_latency_test(
            prompts=["What is deep learning?"] * concurrency,
            concurrency=concurrency
        )
    results['progressive_concurrency'] = prog_results
    
    # 10. Cyclic Load
    cycle_results = []
    for _ in range(3):  # 3 cycles
        for rps in [1, 3, 5, 3, 1]:  # Ramping up and down
            cycle_result = await tester.run_sustained_load_test(
                prompt="What is AI?",
                requests_per_second=rps,
                duration_seconds=10
            )
            cycle_results.append({"rps": rps, "results": cycle_result})
    results['cyclic_load'] = cycle_results
    
    return results

# Run tests
results = await run_optimized_tests()
print(json.dumps(results, indent=2))
