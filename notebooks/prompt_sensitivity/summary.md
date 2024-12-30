# Exploring Prompt Sensitivity in Claude: Insights from New Research on LLM Uncertainty

Recent research by [Aichberger et al. (2024)](https://arxiv.org/pdf/2412.15176) introduces a paradigm shift in how we think about uncertainty estimation in large language models. While traditional approaches rely on sampling multiple outputs to gauge uncertainty, their work suggests that a simpler approach - looking at the likelihood of the most probable output - can be equally effective.

Let's explore how this relates to prompt sensitivity in Claude.

## Experimental Design

Our experiment tests different prompt variations:
- Extra spaces (start/end/double) 
- Capitalization changes (ALL CAPS/lowercase)
- Added punctuation (., ?, !)
- Format changes (newlines)

Key test prompts:
- Explanatory: "Explain how photosynthesis works"
- Creative: "Write a short poem about the moon" 
- Technical: "What are Python's key features"

This aligns with Aichberger et al.'s focus on question-answering tasks, though they primarily used standardized datasets (TriviaQA, SVAMP, NQ).

## Key Findings

Our results showed several interesting parallels with Aichberger's findings:

1. Response Stability
- Minor formatting changes generally preserved core semantic content
- More significant variation appeared with creative vs factual prompts
- Consistent with their finding that likelihood scores effectively capture semantic stability

2. Impact of Sampling
- Like Aichberger et al., we found that sampling multiple outputs often added computational overhead without proportional benefits
- Single "most likely" outputs (via greedy decoding in their case) proved surprisingly reliable

3. Role of Temperature
- Lower temperatures produced more consistent outputs
- Aligns with their observation that beam search and low-temperature sampling converge to similar high-likelihood outputs

## Key Differences

While Aichberger focused on uncertainty estimation for correctness prediction, our study examined prompt engineering stability. However, both point to an important principle: LLM behavior may be more predictable and measurable through simple likelihood-based metrics than previously thought.

## Practical Implications

1. Prompt Engineering
- Focus on semantic clarity over formatting perfection
- Use simple, direct prompts when possible
- Consider likelihood scores as stability indicators

2. Uncertainty Handling  
- Single high-quality outputs may be preferable to multiple samples
- Temperature control offers reliable output stability
- Monitor likelihood scores for potential quality issues

3. Computational Efficiency
- Avoid unnecessary multiple sampling when single outputs suffice
- Use greedy decoding for stable outputs
- Consider likelihood thresholds for quality control

## Conclusion

Our findings complement Aichberger et al.'s work in suggesting that LLM behavior may be more predictable and efficiently measurable than previously assumed. While they focused on uncertainty estimation through likelihood scores, our prompt sensitivity results suggest this principle extends to prompt engineering stability as well.

Both studies point toward simpler, more computationally efficient approaches to working with LLMs - whether for uncertainty estimation or prompt engineering.

_Future research could explore combining these insights - perhaps using likelihood-based metrics to automatically optimize prompt stability while maintaining output quality._

The full code and detailed analysis are available in the [Colab notebook](https://colab.research.google.com/github/wesslen/llm-experiments/blob/main/notebooks/prompt_sensitivity/claude.ipynb).
