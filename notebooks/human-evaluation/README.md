## Initial Hypothesis and Strategy

Evaluation involves:
- 130 contracts (both master agreements and amendments)
- 10 vendors
- 5 questions per contract in different styles
- 3 SMEs for evaluation
- Goal: Minimize time while ensuring quality evaluation

### Round 1: Calibration and Coverage Strategy

**Hypothesis**: A mixed approach of shared and unique examples will provide both calibration data for measuring inter-annotator agreement (IAA) and broader coverage of different contract types and vendors.

**Sampling Strategy**:
1. **Common Calibration Set (25 queries)**:
- Select 5 contracts covering different vendors
- Include both master agreements and amendments
- All 5 questions per contract to evaluate style variations
- All 3 SMEs evaluate these 25 queries

2. **Unique Evaluation Sets (25 queries per SME)**:
- Each SME receives 25 unique queries not seen by others
- Distribute evenly across remaining vendors and contract types
- Total: 75 unique queries + 25 common queries = 100 queries evaluated

3. **Tracking Metadata**:
- Record contract type (master/amendment)
- Record vendor
- Record question style/type
- Track evaluation time per query

## Round 2 and 3 Proposal

### Round 2: Targeted Expansion

**Hypothesis**: Focusing on problematic areas identified in Round 1 will yield the most efficient improvements.

**Strategy**:
1. Analyze Round 1 results to identify:
- Contracts/vendors with highest rejection rates
- Question styles causing the most disagreement
- Parent-child relationship issues

2. **Common Calibration Set (20 queries)**:
- Keep 10 queries from Round 1 that showed medium agreement
- Add 10 new queries focused on areas needing improvement

3. **Targeted Evaluation (40 queries per SME)**:
- 20 queries overlap for all SMEs
- 40 unique queries per SME
- Total: 140 queries evaluated
- Introduce parent-child relationship queries 
- Add metadata-based queries

### Round 3: Comprehensive Evaluation

**Hypothesis**: A more comprehensive evaluation covering edge cases and implementing query rewriting will provide final validation.

**Strategy**:
1. **Common Calibration Set (25 queries)**:
- Select examples that still show disagreement from Round 2
- Include edge cases identified in previous rounds

2. **Expanded Evaluation (50 queries per SME)**:
- 25 queries overlap for all SMEs
- 50 unique queries per SME
- Total: 175 queries evaluated
- Implement query rewriting techniques
- Focus on complex scenarios (e.g., amendments referencing multiple parent contracts)

## Implementation Recommendations

1. **Randomize query order** to prevent order bias
2. **Time-box evaluation sessions** (e.g., 45-60 minutes) to maintain SME focus
3. **Provide clear evaluation guidelines** with examples of accept/reject criteria
4. **Track time per query** to identify problematic question types
5. **Implement a simple feedback loop** after each round to refine the process

## Round 1: Working Definition of "Acceptable" Query

A query is considered **acceptable** in Round 1 if it meets the following criteria:

1. **Clarity and Specificity**: The query is clearly formulated, specific enough to target relevant contract information, and free from ambiguity that would make it difficult to determine the correct answer.

2. **Relevance to Contracts**: The query seeks information that would reasonably be found within the contract documents being evaluated, rather than asking for external information.

3. **Business Value**: The query represents a realistic information need that would be asked by actual users of the supply chain RAG system (e.g., procurement specialists, legal teams, contract managers).

4. **Answer Determinability**: The query has a determinable answer based solely on the content of the contract itself (without requiring cross-referencing to other contracts at this stage).

5. **Linguistic Quality**: The query is grammatically correct and uses appropriate terminology related to supply chain and contract management.

### Rejection Criteria for Round 1:

A query should be rejected if it:
- Is ambiguous or too vague to target specific information
- Contains factual errors about the contract or vendor
- Requires information not contained within the single contract being examined
- Uses inconsistent or incorrect technical terminology
- Is redundant with other queries in the evaluation set
- Would be unlikely to be asked in real-world scenarios

## Evolution of Definition in Rounds 2 & 3

### Round 2: Evolution to Include Relationships

In Round 2, the definition expands to include:

1. **Parent-Child Relationship Awareness**: Queries that appropriately reference relationships between master agreements and amendments are acceptable.

2. **Metadata Integration**: Queries that effectively utilize contract metadata (e.g., effective dates, parties, contract values) to constrain or contextualize the query are acceptable.

3. **Contextual Relevance**: Queries that demonstrate awareness of the broader contractual context (e.g., "According to amendment 2, how does the payment schedule differ from the master agreement?") are acceptable.

4. **Multi-Contract Awareness**: Queries that reference information across related contracts (e.g., "Has the liability cap changed in any amendments to the master agreement?") are acceptable.

### Round 3: Full Sophistication

In Round 3, the definition reaches full sophistication:

1. **Query Rewriting Compatibility**: Queries that can be effectively rewritten by the system to improve retrieval performance are acceptable.

2. **Complex Scenarios**: Queries addressing complex scenarios involving multiple contract elements (e.g., "What obligations apply if vendor X terminates under section 14.2 after the third amendment's effective date?") are acceptable.

3. **Edge Cases**: Queries that target known edge cases in the contract language or structure are acceptable.

4. **Comparison Queries**: Queries that ask for comparisons between multiple vendors' contracts on similar topics are acceptable.

5. **Inference-Based Queries**: Queries requiring reasonable inferences from multiple contract sections rather than explicit statements are acceptable.

## Implementation Notes

For Round 1, I recommend:
- Creating an evaluation rubric with examples of acceptable/unacceptable queries for SMEs
- Including a brief explanation field for rejections to capture specific reasons
- Tracking acceptance rates by query style to inform future query generation
- Setting a threshold (e.g., 2 out of 3 SMEs must accept) for determining overall acceptability

This progressive definition allows you to start with basic query quality in Round 1, then gradually introduce more sophisticated evaluation criteria as your RAG system and evaluation process mature.​​​​​​​​​​​​​​​​



