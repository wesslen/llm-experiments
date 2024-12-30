# Exploring Prompt Sensitivity with Claude 3
An experiment analyzing how small changes in prompts affect Claude's responses using DSPy.
## Key Setup
- Used DSPy to test Claude 3 responses to prompt variations
- Tested changes in spacing, punctuation, capitalization across different types of prompts
- Analyzed response consistency and variation
## Experiment Design
Tested prompt variations including:
- Extra spaces (start/end)
- Double spacing
- All caps vs lowercase
- Added punctuation (., ?, !)
- Newlines
- No spaces
## Sample Test Cases
Examined responses across diverse prompts:
- Explanatory: "Explain how photosynthesis works"
- Creative: "Write a short poem about the moon"
- Technical: "What are the key features of Python"
- Short: "Summarize"
- Scientific: "Explain mitochondrial DNA vs nuclear DNA"
- Database design
- SQL debugging
## Key Findings
The analysis revealed:
- Claude showed remarkable consistency in core content despite surface-level prompt changes
- Minor formatting changes generally did not significantly alter response meaning
- Some variations (like ALL CAPS) occasionally produced slightly different phrasings or examples
- Response length and structure remained fairly stable across variations
## Key Tools Used
- DSPy for experiment orchestration
- Pandas for data analysis
- Difflib for response comparison
- IPython display for visualizing differences
## Implications
- Claude demonstrates robust response patterns regardless of minor prompt variations
- Suggests strong semantic understanding beyond surface text features
- Helpful for understanding Claude's prompt processing behavior
The full code and detailed analysis are available in the [Colab notebook](https://colab.research.google.com/github/wesslen/llm-experiments/blob/main/notebooks/prompt_sensitivity/claude.ipynb).

_Future research could explore combining these insights - perhaps using likelihood-based metrics to automatically optimize prompt stability while maintaining output quality._

The full code and detailed analysis are available in the [Colab notebook](https://colab.research.google.com/github/wesslen/llm-experiments/blob/main/notebooks/prompt_sensitivity/claude.ipynb).
