# A Survey on Reinforcement Learning for Large Language Model Reasoning

## TL;DR
- Reinforcement Learning (RL) has transitioned from superficial human preference alignment (RLHF) to powering advanced multi-step logical reasoning and "slow-thinking" paradigms in Large Language Models [1][2].
- Foundational algorithms like Proximal Policy Optimization (PPO) and Direct Preference Optimization (DPO) established robust paradigms for aligning LLMs by maximizing reward model objectives or optimizing preferences in closed form [1][3][4].
- Reasoning tasks benefit significantly from reward modeling granularity, contrasting outcome-based supervision with step-by-step process supervision (PRMs) to evaluate intermediate logical steps [5][6][7].
- Recent advances (2023–2025) integrate reinforcement learning with test-time compute scaling and search algorithms (such as Monte Carlo Tree Search) to match OpenAI o1-style long chain-of-thought capabilities [2][8][9][10].

## Background
Aligning and training large language models (LLMs) to perform complex reasoning requires moving beyond standard next-token prediction objectives [1]. Early foundational work in Reinforcement Learning from Human Feedback (RLHF), exemplified by InstructGPT [1], demonstrated that fine-tuning pre-trained language models via human preference data substantially improves truthfulness, safety, and task adherence. The standard RLHF workflow involves three stages: supervised fine-tuning (SFT) on expert demonstrations, training a reward model (RM) on human preference comparisons, and optimizing the language model policy using Proximal Policy Optimization (PPO) with a per-token Kullback-Leibler (KL) divergence penalty to prevent policy collapse [1]. 

While PPO-based RLHF proved successful, its training instability and high computational overhead spurred alternative preference tuning paradigms. Direct Preference Optimization (DPO) eliminated the need for a separate reward model and reinforcement learning loop by formulating a closed-form analytical mapping between reward functions and optimal policies [3]. By reparameterizing the reward function in terms of the policy and reference model, DPO optimizes the preference objective directly via binary cross-entropy loss [3]. 

However, standard alignment objectives optimized primarily for response-level preferences often fall short on multi-step reasoning tasks such as mathematics, coding, and symbolic deduction. This limitation has driven a major evolution toward reinforcement learning for complex LLM reasoning, incorporating rigorous reward modeling and test-time search [2][8].

## Foundational Preference Optimization and Policy Gradient Algorithms
Standard policy optimization in LLMs relies heavily on policy gradient methods that balance sample efficiency and stability [4]. Proximal Policy Optimization (PPO) addresses the instability of traditional policy gradients by introducing a clipped surrogate objective function that permits multiple gradient epochs per data batch while bounding policy updates [4]. This mechanism underpins most large-scale RL-driven alignment and reasoning pipelines [1][2].

Despite PPO's dominance, optimization complexity has led to alternative formulations. Direct Preference Optimization (DPO) bypasses reinforcement learning entirely by analytically expressing the reward function as $r(x,y)=\beta\log\frac{\pi(y\mid x)}{\pi_{\text{ref}}(y\mid x)}$, allowing models to be optimized directly on preference pairs using standard cross-entropy loss [3]. Empirical analyses demonstrate that DPO matches or exceeds PPO performance in response quality and alignment tasks while substantially simplifying infrastructure requirements [3]. Nevertheless, for complex reasoning domains requiring long trajectory exploration, policy gradient methods and reinforcement learning remain essential for guiding models through dense decision spaces [2].

## Reward Modeling: Outcome Supervision vs. Process Supervision
A central challenge in applying reinforcement learning to LLM reasoning is defining reliable reward signals for multi-step problems [5][7]. Outcome reward models (ORMs) evaluate only the final answer (e.g., whether a math word problem solution is correct) [6]. While ORMs are cost-effective and easy to collect at scale, they suffer from credit assignment issues, rewarding correct final answers even if they derive from flawed intermediate reasoning (spurious correctness) [6].

To address this, process reward models (PRMs) evaluate intermediate reasoning steps, providing dense, fine-grained supervision [5][7]. Comparing process and outcome supervision on mathematical reasoning datasets such as GSM8K confirms that process-based supervision is vital for ensuring faithful intermediate derivations [6]. However, traditional PRMs require extensive human annotations at every step, making human data collection prohibitively expensive [5][7]. 

Recent research addresses this bottleneck through automated process supervision and implicit reward learning [5][11][7]. Techniques such as OmegaPRM employ divide-and-conquer Monte Carlo Tree Search (MCTS) algorithms to automate process supervision data collection without human intervention [11]. Similarly, outcome-only reinforcement learning frameworks like TIPS (Thinking-Induced Process Supervision) train generative PRMs from outcome signals alone [5], while other work demonstrates that implicit PRMs can be derived at zero extra cost by training standard ORMs on cheaper response-level outcome labels [7].

## Test-Time Compute Scaling and Search-Based Reasoning
Recent developments (2023–2025) highlight a profound paradigm shift toward test-time scaling, where models allocate substantial computational resources during inference to solve complex reasoning problems [2][8][9]. Mirroring scaling laws observed in training, increasing inference-time compute yields predictable performance gains [2]. This trajectory was popularized by reasoning systems like OpenAI o1, which employ large-scale reinforcement learning to generate an extensive internal chain of thought before emitting an answer [10].

To systematically explore reasoning paths, inference-time frameworks integrate reinforcement learning with heuristic search algorithms [2][8][9]. Using Markov Decision Process (MDP) formulations, LLM reasoning is structured around modular components comprising a policy model, a transition model, and an evaluator (such as a PRM or ORM) [9]. Search strategies such as Best-of-N, Beam Search, Tree-of-Thoughts (ToT), and Monte Carlo Tree Search (MCTS) enable models to systematically explore, evaluate, and backtrack through alternative solution trajectories [2][9]. For instance, OpenAI's reasoning models achieved massive performance boosts on competitive programming tasks (such as the International Olympiad in Informatics) by combining large-scale RL training with extensive test-time solution sampling and selection [10].

## Trends and open problems
The convergence of reinforcement learning and test-time scaling has transformed LLMs into capable reasoning engines [2][8], yet several key limitations and open problems remain:
- **Reward Hacking and Generalization:** Reward models, whether ORMs or PRMs, are prone to exploitation where the policy maximizes the reward score without genuine logical improvement [5][7]. Developing robust, un-hackable verifiers is an ongoing challenge.
- **Compute Overhead of Test-Time Search:** While test-time scaling dramatically improves reasoning accuracy, executing complex search algorithms like MCTS or generating thousands of rollout candidates incurs prohibitive latency and computational costs [2][10].
- **Scalability of Automated Supervision:** Although automated techniques like OmegaPRM and outcome-induced process supervision mitigate human annotation bottlenecks [5][11], scaling these methods to domains with sparse verification criteria or highly subjective reasoning remains difficult.
- **Theoretical Understanding of Implicit Reasoning:** The precise mechanisms by which reinforcement learning induces internal chain-of-thought generation and long-horizon planning in transformer architectures are still theoretically underdeveloped, relying largely on empirical validation [2][8].

## References
[1] Training language models to follow instructions with human feedback. arxiv. https://arxiv.org/abs/2203.02155 (2022-03-04)
[2] A Survey on Test-Time Scaling in Large Language Models: What, How, Where, and How Well. web. https://arxiv.org/html/2503.24235v3 (2025-05-04)
[3] Direct Preference Optimization: Your Language Model is Secretly a Reward Model. arxiv. https://arxiv.org/abs/2305.18290 (2023-05-29)
[4] Proximal Policy Optimization Algorithms. arxiv. https://arxiv.org/abs/1707.06347 (2017-07-20)
[5] Inducing Process Supervision from Outcome-Only Reinforcement Learning. arxiv. https://arxiv.org/abs/2609.36641 (2026-09-29)
[6] Solving math word problems with process- and outcome-based feedback. hf-search. https://huggingface.co/papers/2211.14275 (2022-11-25)
[7] Free Process Rewards without Process Labels. arxiv. https://arxiv.org/abs/2412.01981 (2024-12-02)
[8] Towards Large Reasoning Models: A Survey of Reinforced Reasoning with Large Language Models. web. https://arxiv.org/html/2501.09686 (n.d.)
[9] A Survey on Test-Time Scaling in Large Language Models: Tasks, LLM Profiling, Search Algorithms, and Relevant Frameworks. web. https://arxiv.org/html/2501.10069 (n.d.)
[10] Learning to reason with LLMs. web. https://openai.com/index/learning-to-reason-with-llms/ (2024-09-12)
[11] Improve Mathematical Reasoning in Language Models by Automated Process Supervision. hf-search. https://huggingface.co/papers/2406.06592 (2024-06-05)
