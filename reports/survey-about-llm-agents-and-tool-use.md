# Survey on LLM Agents and Tool Use: Architectures, Multi-Agent Collaboration, Uncertainty, and Skill Acquisition

## TL;DR
- Large language model (LLM) agents leverage external APIs, calculators, and tools to overcome inherent limitations in factual grounding, exact calculation, and real-time reasoning [1][2].
- Foundational neuro-symbolic and self-supervised paradigms, such as MRKL and Toolformer, established the core capabilities for language models to independently invoke external tools [1][2].
- Specialized models like Gorilla address API hallucination and incorrect argument generation across massive API collections [3].
- Recent daily papers and systematic surveys investigate multi-agent collaboration, black-box optimization benchmarks, multi-turn intent preservation, and agentic skill acquisition [4][5][6][7][8][9].

## Background
Large language model (LLM) agents have emerged as a powerful paradigm for extending static generative models into active problem solvers capable of interacting with external software environments [1][2]. While foundational language models exhibit remarkable linguistic fluency, they remain constrained by parametric memory limitations, inability to perform precise arithmetic, and lack of real-time data access [1][2]. 

To overcome these boundaries, foundational neuro-symbolic architectures such as MRKL (Modular Reasoning, Knowledge and Language) introduced a systems approach that routes sub-tasks between neural language models and discrete symbolic modules [1]. Building upon this, self-supervised learning paradigms like Toolformer demonstrated that language models can autonomously teach themselves when to invoke APIs, format arguments, and incorporate responses into token prediction [2]. Concurrently, specialized fine-tuning approaches like Gorilla established robust capabilities for connecting LLMs with massive and rapidly changing API collections [3]. Recent advancements further refine these interactions through agentic skill frameworks and uncertainty quantification [4][7].

## Foundational Architectures and Tool-Use Paradigms
Early architectures established the blueprint for tool integration by separating linguistic generation from exact computation and information retrieval [1][2]. MRKL systems pioneered this neuro-symbolic decoupling, allowing an LLM router to direct specialized queries to external knowledge sources [1]. However, relying solely on human-annotated tool use limits scaling [2]. Toolformer addressed this by-self-supervised training where models generate API calls as potential annotations, filtering them based on whether they reduce prediction perplexity [2].

As the volume and complexity of available APIs expanded, fine-tuning alone became insufficient for dynamic tool selection [3]. Gorilla addressed API hallucination and incorrect argument generation by training models specifically on API documentation and semantic input requirements [3]. Concurrently, recent studies on uncertainty estimation (U-Space) highlight that language models often present incorrect tool invocation conclusions with an authoritative tone, motivating uncertainty quantification mechanisms to improve reliability [4].

## Multi-Agent Collaboration and Optimization Benchmarks
Beyond single-agent tool execution, complex scientific and engineering tasks increasingly rely on multi-agent collaboration and black-box optimization (BBO) benchmarks [5][8]. Agentic BBO studies combine task semantics, optimization tools, and feedback-driven decision-making to evaluate LLM agents on expensive function optimization [5]. 

At the same time, systematic surveys on multi-agent systems emphasize that sustained coordination requires integrated approaches for continuous diagnosis, failure attribution, and self-evolution across structured interaction stages [8]. These multi-agent architectures manage error propagation and localized hallucinations through structured decomposition and supervisory critique loops [8].

## Multi-Turn Dialogue Intent and Dialogue Robustness
Maintaining reliable tool invocation across multi-turn interactions introduces significant dialogue challenges [6]. When a user proposes a temporary modification during a multi-turn task and subsequently rejects it, models often become derailed by merely mentioning the rejected change [6]. 

To address this, benchmarks such as Intent-Eval evaluate model robustness across tool actions, code, databases, and mathematics, demonstrating that intent preservation is critical for robust agentic workflows in multi-turn environments [6].

## Agentic Skills and Architectural Scaffolding
As agent capabilities expand beyond basic API calls, recent research emphasizes procedural agentic skills—packaging procedural knowledge with applicability conditions and execution policies [7][9]. Systems of knowledge (SoK) on agentic skills highlight that modular skill loading enables flexible deployment and governance across diverse environments [7].

Furthermore, architectural analysis of coding agent scaffolding across open-source implementations reveals 12 distinct dimensions spanning control structures, tool interfaces, and resource management [10], guiding the design of more modular and secure agent execution platforms.

## Trends and open problems
The evolution of LLM agents and tool use has shifted from static single-turn API calls to dynamic, multi-agent, skill-augmented ecosystems [7][8][9]. Key emerging trends include modular skill loading [9], intent preservation benchmarks for multi-turn dialogues [6], and agentic black-box optimization frameworks [5].

Nonetheless, several open problems remain unresolved [4][6][8]. First, language models frequently present incorrect tool conclusions with authoritative confidence, necessitating more reliable uncertainty quantification [4]. Second, multi-turn dialogue derailment caused by temporary user suggestions remains a persistent vulnerability [6]. Third, mitigating cumulative error propagation in multi-agent collaboration requires advanced continuous diagnosis and self-evolution mechanisms [8].

## References
[1] MRKL Systems: A modular, neuro-symbolic architecture that combines large language models, external knowledge sources and discrete reasoning. arxiv. https://arxiv.org/abs/2205.00445 (2022-05-01)
[2] Toolformer: Language Models Can Teach Themselves to Use Tools. arxiv. https://arxiv.org/abs/2302.04761 (2023-02-09)
[3] Gorilla: Large Language Model Connected with Massive APIs. arxiv. https://arxiv.org/abs/2305.15334 (2023-05-24)
[4] U-Space: Uncovering When and Why Uncertainty Arises in Language Models. hf-daily. https://huggingface.co/papers/2610.09087 (2026-10-06)
[5] A Closer Look at Agentic BBO: Benchmarking LLM Agents for Black-Box Optimization. hf-daily. https://huggingface.co/papers/2610.12183 (2026-10-08)
[6] You Changed Your Mind, The Model Didn't: Demystifying Intent in Multi-Turn Dialogue. hf-daily. https://huggingface.co/papers/2610.06496 (2026-10-05)
[7] SoK: Agentic Skills -- Beyond Tool Use in LLM Agents. hf-search. https://huggingface.co/papers/2602.20867 (2026-02-24)
[8] Beyond Individual Intelligence: Surveying Collaboration, Failure Attribution, and Self-Evolution in LLM-based Multi-Agent Systems. hf-search. https://huggingface.co/papers/2605.14892 (2026-05-14)
[9] Agent Skills for Large Language Models: Architecture, Acquisition, Security, and the Path Forward. hf-search. https://huggingface.co/papers/2602.12430 (2026-02-12)
[10] Agentic Coding Architectures. hf-search. https://huggingface.co/papers/2604.03515 (2026-04-10)
