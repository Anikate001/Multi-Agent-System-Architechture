# SECTION 1: MACHINE LEARNING — 15 S-TIER PROJECTS

> Classical ML projects focusing on tabular data, time-series, anomaly detection, and traditional algorithms.
> These projects demonstrate strong foundations in statistics, feature engineering, and production ML.

---

## PROJECT 1: Real-Time Anomaly Detection for IoT Sensor Networks

**🎯 The Hook:** Built a distributed anomaly detection system that monitors 50K+ simulated IoT sensors in real-time, achieving 97% precision with <100ms latency using Isolation Forests and streaming algorithms.

**Difficulty:** ████████░░ (8/10)

### 🧠 Why S-Tier?
- STREAMING ML (not batch) — processes 50K messages/second in real-time
- Unsupervised learning with automatic drift detection and retraining
- Production-grade with 99.9% uptime, monitoring, and alerting
- Most freshers do batch ML — this is TRUE real-time system design
- Demonstrates distributed systems knowledge (Kafka, Redis, state management)

### 🛠️ Tech Stack (100% Free Tier)
- **Compute:** Google Colab (training), Railway.app (500 hrs/month free)
- **Streaming:** Upstash Redis (10K msgs/day) OR Confluent Kafka Cloud
- **Storage:** Supabase PostgreSQL + TimescaleDB extension (500MB free)
- **Dashboard:** Streamlit Cloud + Grafana Cloud (both free)
- **Alerts:** Slack Webhooks (free)

### 📐 Architecture Overview
1. IoT Sensor Simulator → generates 50K sensor streams with 2% anomaly injection
2. Kafka/Redis Stream → message queue with partitioning by sensor_id
3. Stream Processor (Faust) → sliding window feature engineering (100-reading windows)
4. Isolation Forest Model → scores each reading with anomaly score
5. Alert Pipeline → triggers on threshold violations, logs to PostgreSQL
6. Drift Detector (ADWIN) → monitors score distribution, triggers auto-retrain
7. Grafana Dashboard → real-time visualization of anomalies and metrics

### 🔨 Implementation Phases
- **Week 1: Sensor Simulation (7 days)** — Build realistic IoT sensor simulator with normal/anomaly patterns (spikes, drift, stuck sensors). Generate 50K concurrent sensor streams.
- **Week 2: Streaming Pipeline (7 days)** — Set up Kafka/Redis streaming infrastructure. Implement Faust stream processor with sliding window state management. Build feature engineering pipeline.
- **Week 3: Model Training & Drift Detection (7 days)** — Train Isolation Forest on historical data. Implement ADWIN drift detector. Build auto-retraining pipeline that triggers on distribution shifts.
- **Week 4: Dashboard & Monitoring (7 days)** — Build Streamlit real-time dashboard. Set up Grafana for time-series visualization. Implement Slack alerting. Add model performance tracking.

### ⚡ Key Challenges & Solutions
- **Challenge:** Latency — How to process 50K msgs/sec with <100ms response?
  - **Solution:** Use in-memory state (Redis/Faust Tables), pre-load model, batch feature computation, and optimize with Numba JIT compilation for hot paths.
- **Challenge:** Model Drift — Performance degrades as sensor behavior changes
  - **Solution:** Implement ADWIN drift detector monitoring anomaly score distribution. Auto-trigger retraining on drift with last 100K normal samples from TimescaleDB.
- **Challenge:** State Management — Tracking 50K sensor windows crashes memory
  - **Solution:** Use LRU cache with TTL for inactive sensors. Persist critical state to Redis. Implement stateful stream partitioning by sensor_id.

### 🎓 What You'll Learn (Interview Gold)
- Streaming ML algorithms (Isolation Forest online scoring)
- Distributed systems (Kafka partitioning, stream processing)
- Unsupervised anomaly detection (no labeled data required)
- Production monitoring (drift detection, alerting, dashboards)
- Time-series databases (TimescaleDB for sensor data)
- Real-time system design (latency optimization, stateful processing)

### 🔥 Interview Talking Points
- **Q:** How did you handle 50K sensors without running out of memory?
  - **A:** I used Faust stateful tables with LRU eviction for inactive sensors. Each sensor maintains a 100-reading sliding window (~4KB). With partitioning by sensor_id, each processor handles ~10K sensors = 40MB state. Inactive sensors (no data in 5min) are evicted and reloaded on next message.
- **Q:** How do you know if the model is still accurate over time?
  - **A:** I track two metrics: (1) Precision/Recall on injected ground-truth anomalies (2% injection rate), and (2) ADWIN drift detector on anomaly score distribution. When ADWIN detects drift, I auto-trigger retraining on last 100K normal readings, achieving <1% accuracy degradation.
- **Q:** What was the biggest technical challenge?
  - **A:** Latency. Initial implementation took 300ms per prediction. I optimized by: (1) Pre-loading sklearn model, (2) Vectorizing feature computation with NumPy, (3) Using RobustScaler.transform instead of fit_transform, (4) Batching Redis writes. Final latency: 87ms p95.

**📊 Portfolio Impact:** ⭐⭐⭐⭐⭐
**Resume Bullet:** Engineered real-time anomaly detection system processing 50K+ IoT sensors using Isolation Forests and Kafka streaming, achieving 97% precision with <100ms latency and auto-retraining on drift detection

### 🚀 Deployment Strategy
- Deploy stream processor on Railway.app (500 hrs/month free)
- Host Streamlit dashboard on Streamlit Cloud
- Configure Grafana Cloud for time-series visualization
- Set up Slack webhook for anomaly alerts
- Add GitHub Actions CI/CD for automated testing

---

## PROJECT 2: Multi-Armed Bandit Recommendation Engine with Thompson Sampling

**🎯 The Hook:** Built a production recommendation system that dynamically learns user preferences in real-time using Thompson Sampling, increasing click-through rates by 34% over static recommendations with provable regret bounds.

**Difficulty:** ███████░░░ (7/10)

### 🧠 Why S-Tier?
- Online learning — NO batch retraining required, learns continuously
- Bayesian inference (Beta distributions) — shows deep statistical understanding
- Solves exploration-exploitation tradeoff with theoretical guarantees
- A/B tested with REAL metrics (34% CTR lift)
- Most freshers build static recommenders — this ADAPTS in real-time

### 🛠️ Tech Stack (100% Free Tier)
- **Compute:** Railway.app (API server)
- **Storage:** Supabase PostgreSQL (Beta distribution parameters)
- **API:** FastAPI with async endpoints
- **Analytics:** Streamlit dashboard
- **Monitoring:** Grafana for regret tracking

### 📐 Architecture Overview
1. User Request → FastAPI endpoint receives recommendation request
2. Thompson Sampling → Sample from Beta(α, β) for each item
3. Top-K Selection → Return items with highest sampled CTRs
4. User Interaction → Track clicks/no-clicks
5. Posterior Update → α += 1 (click) or β += 1 (no-click)
6. State Persistence → Save updated parameters to PostgreSQL
7. A/B Test Framework → 80% Thompson vs 20% baseline (random)
8. Analytics Dashboard → Track CTR lift, regret, convergence

### 🔨 Implementation Phases
- **Week 1: Core Algorithm (7 days)** — Implement Thompson Sampling with Beta distributions. Build FastAPI endpoints for recommend/feedback. Set up PostgreSQL state persistence.
- **Week 2: Contextual Extension (7 days)** — Extend to Contextual Thompson Sampling using Bayesian Ridge Regression. Learn CTR as function of context (time, device, user features).
- **Week 3: A/B Testing Framework (7 days)** — Build traffic splitter (80/20 treatment/control). Implement statistical significance testing (t-test). Track metrics in PostgreSQL.
- **Week 4: Dashboard & Analysis (7 days)** — Build Streamlit dashboard showing posterior distributions, CTR lift, regret bounds. Visualize convergence and uncertainty.

### ⚡ Key Challenges & Solutions
- **Challenge:** Cold-start problem — new items have no data
  - **Solution:** Initialize with Beta(1,1) uniform prior. Thompson Sampling naturally explores high-uncertainty items. Built contextual variant using item metadata for warm-start.
- **Challenge:** How to measure success without ground truth?
  - **Solution:** A/B test against random baseline, tracking CTR lift. Compute Bayesian regret and validate against theoretical O(√T log T) bound.
- **Challenge:** State consistency — concurrent updates corrupt α/β
  - **Solution:** PostgreSQL row-level locking with SELECT FOR UPDATE. Optimistic locking with version counter.

### 🎓 What You'll Learn
- Bayesian inference and conjugate priors (Beta-Binomial)
- Reinforcement learning (exploration-exploitation, regret minimization)
- Online learning algorithms (no batch retraining)
- A/B testing methodology and statistical significance
- Production API design (FastAPI, async, background tasks)

### 🔥 Interview Talking Points
- **Q:** Why Thompson Sampling over ε-greedy or UCB?
  - **A:** Thompson Sampling is probability matching — explores proportional to probability of being optimal. I measured 15% faster convergence vs ε-greedy in my A/B test.
- **Q:** How do you handle cold-start?
  - **A:** New items start with Beta(1,1) uniform prior. I also built contextual variant using Bayesian Ridge Regression leveraging item features.
- **Q:** What's your regret bound?
  - **A:** O(√T log T) Bayesian regret. Empirical plot tracks theoretical curve within 5% after 10K interactions.

**📊 Portfolio Impact:** ⭐⭐⭐⭐
**Resume Bullet:** Developed real-time recommendation engine using Thompson Sampling (Bayesian bandits), achieving 34% CTR lift with provable O(√T log T) regret bounds, deployed with FastAPI and A/B testing framework

---

## PROJECT 3: Distributed Gradient Boosting with XGBoost on 10M+ Samples

**🎯 The Hook:** Trained XGBoost on 10M+ transaction records achieving 0.98 AUC for fraud detection, using Dask for distributed training and SHAP for interpretability — all on Colab free tier.

**Difficulty:** ███████░░░ (7/10)

### 🧠 Why S-Tier?
- Handles BIG data (10M+ rows) on FREE compute via Dask distributed
- Production fraud detection (high-stakes, imbalanced, real-world)
- Model interpretability with SHAP (required for financial ML)
- Feature engineering for tabular data (80% of real ML jobs)

### 🛠️ Tech Stack: Colab + Dask + XGBoost/LightGBM/CatBoost + SHAP + HuggingFace
### Key Metrics: 0.98 AUC, 0.85 F1, handled 0.17% fraud rate
### Resume Bullet: Built distributed fraud detection on 10M+ transactions using Dask XGBoost, achieving 0.98 AUC with SHAP interpretability on Colab free tier

---

## PROJECT 4: Self-Supervised Contrastive Learning (SimCLR) from Scratch

**🎯 The Hook:** Trained SimCLR from scratch on ImageNet subset to learn visual representations WITHOUT labels, achieving 87% linear probe accuracy — demonstrating deep self-supervised learning.

**Difficulty:** █████████░ (9/10)

### 🧠 Why S-Tier?
- Self-supervised learning — no labels required (cutting-edge research)
- Implements SimCLR from scratch (not just fine-tuning)
- NT-Xent contrastive loss with data augmentation strategies
- Trained on Colab TPU free tier
- Most freshers fine-tune — you BUILT the pretraining pipeline

### Key Metrics: 87% linear probe on ImageNet, 95% on CIFAR-10 transfer
### Resume Bullet: Implemented SimCLR self-supervised learning from scratch, training ResNet-50 on 100K unlabeled images to achieve 87% linear probe accuracy using Colab TPU

---

## PROJECT 5: Graph Neural Network for Fraud Detection in Transaction Networks

**🎯 The Hook:** Built GNN-based fraud detector modeling transactions as a graph, leveraging network structure to detect fraud rings with 94% accuracy — outperforming traditional ML by 12% on cold-start users.

**Difficulty:** ████████░░ (8/10)

### 🧠 Why S-Tier?
- Graph ML — emerging field, most freshers have zero graph experience
- GNN (GraphSAGE) implementation from scratch with PyTorch Geometric
- Handles cold-start via network structure (neighbor aggregation)
- Deployed on Neo4j with interactive fraud ring visualization

### Key Metrics: 94% accuracy, 12% lift on cold-start, 200K nodes
### Resume Bullet: Developed GNN-based fraud detection using GraphSAGE on 200K-node transaction network, achieving 94% accuracy with 12% cold-start lift — deployed on Neo4j

---

## PROJECT 6: Survival Analysis for Customer Churn (Cox Proportional Hazards)

**🎯 The Hook:** Built time-to-churn prediction using survival analysis (Cox PH), identifying high-risk customers 30 days before churn with 0.81 concordance index — enabling proactive retention.

**Difficulty:** ███████░░░ (7/10)

### 🧠 Why S-Tier?
- Survival analysis (rare skill, critical for churn/retention)
- Handles censored data (active users = unknown churn time)
- Time-varying covariates, interpretable hazard ratios
- Deployed with proactive alerting system

### Key Metrics: 0.81 C-index, 30-day early warning
### Resume Bullet: Developed survival analysis churn prediction using Cox PH with time-varying covariates, achieving 0.81 C-index for proactive retention

---

## PROJECT 7: Causal Inference for Marketing Attribution (Uplift Modeling)

**🎯 The Hook:** Built causal model measuring TRUE treatment effect of marketing using uplift modeling and propensity score matching — increasing ROI by 28% by targeting persuadables.

**Difficulty:** ████████░░ (8/10)

### 🧠 Why S-Tier?
- Causal inference (not just correlation)
- Uplift modeling segments: persuadables vs lost causes
- Propensity score matching for bias correction
- Advanced stats rarely seen in freshers

### Key Metrics: 28% ROI improvement, CATE estimation
### Resume Bullet: Developed uplift modeling framework using causal inference (propensity score matching, CATE estimation), achieving 28% ROI improvement by targeting persuadables

---

## PROJECT 8: Active Learning for Label-Efficient Medical Diagnosis

**🎯 The Hook:** Built active learning system achieving 93% accuracy with only 20% of labels using uncertainty+diversity sampling — reducing annotation costs by 80% on medical imaging.

**Difficulty:** ███████░░░ (7/10)

### 🧠 Why S-Tier?
- Active learning (label efficiency for expensive annotations)
- Uncertainty + diversity sampling strategies
- Medical imaging domain (high impact)
- Cost-benefit analysis with business value

### Key Metrics: 93% accuracy with 20% labels, 80% cost reduction on ChestX-ray14
### Resume Bullet: Implemented active learning for medical imaging achieving 93% accuracy with only 20% labels using uncertainty+diversity sampling — 80% cost reduction

---

## PROJECT 9: Neural Architecture Search (NAS) for Mobile-Optimized Models

**🎯 The Hook:** Built NAS pipeline discovering CNN architectures optimized for mobile (latency + accuracy), achieving 78% ImageNet accuracy with 50ms CPU inference — outperforming MobileNetV2.

**Difficulty:** █████████░ (9/10)

### 🧠 Why S-Tier?
- AutoML (automated architecture design)
- Multi-objective optimization (accuracy + latency + size)
- Evolutionary algorithms (NSGA-II) for Pareto-optimal search
- Mobile ML constraints and deployment (TFLite, ONNX)

### Key Metrics: 78% ImageNet acc, 50ms CPU, beat MobileNetV2
### Resume Bullet: Built NAS pipeline using NSGA-II multi-objective optimization, discovering mobile CNN achieving 78% ImageNet accuracy with 50ms CPU inference

---

## PROJECT 10: Adversarial Robustness with Certified Defenses (Randomized Smoothing)

**🎯 The Hook:** Built provably robust classifier using randomized smoothing, achieving 68% certified accuracy under L2 attacks (ε=0.5) on CIFAR-10 — with mathematical proof of robustness.

**Difficulty:** █████████░ (9/10)

### 🧠 Why S-Tier?
- Certified defenses (provable guarantees, not heuristics)
- Randomized smoothing with Neyman-Pearson lemma
- Attack generation (PGD, AutoAttack)
- Security-critical ML

### Key Metrics: 68% certified accuracy at ε=0.5, validated with AutoAttack
### Resume Bullet: Developed provably robust classifier using randomized smoothing, achieving 68% certified accuracy against ℓ2 attacks — validated with AutoAttack

---

## PROJECT 11: Meta-Learning for Few-Shot Classification (MAML)

**🎯 The Hook:** Implemented MAML from scratch achieving 89% accuracy on novel classes with only 5 examples — demonstrating rapid adaptation like human learning.

**Difficulty:** █████████░ (9/10)

### 🧠 Why S-Tier?
- Meta-learning (learning to learn) — research-level
- MAML with second-order gradients from scratch
- Few-shot learning demonstrating data efficiency
- Outperformed transfer learning (89% vs 72%)

### Key Metrics: 89% on 5-way 5-shot miniImageNet
### Resume Bullet: Implemented MAML from scratch achieving 89% on 5-way 5-shot miniImageNet with second-order gradient optimization

---

## PROJECT 12: Bayesian Optimization for Hyperparameter Tuning (Multi-Fidelity)

**🎯 The Hook:** Built Bayesian optimization framework with multi-fidelity evaluation achieving 5x faster hyperparameter search than grid/random — optimized XGBoost on 10M rows.

**Difficulty:** ███████░░░ (7/10)

### 🧠 Why S-Tier?
- Bayesian optimization with Gaussian Process surrogates
- Multi-fidelity evaluation (cheap→expensive evals)
- Acquisition functions (EI, UCB, PI)
- Production hyperparameter tuning at scale

### Key Metrics: 5x speedup, 50 trials vs 200 for same performance
### Resume Bullet: Developed Bayesian optimization with multi-fidelity evaluation achieving 5x speedup on XGBoost (10M rows) using GP surrogates

---

## PROJECT 13: Online Learning with Concept Drift Detection (ADWIN + Hoeffding Trees)

**🎯 The Hook:** Built online learning system adapting to concept drift using Hoeffding Trees + ADWIN, maintaining 91% accuracy on non-stationary streams — demonstrating continual learning.

**Difficulty:** ████████░░ (8/10)

### 🧠 Why S-Tier?
- Online learning with real-time model updates
- Concept drift detection (ADWIN, DDM, KSWIN)
- Hoeffding Trees (streaming decision trees)
- Continual learning without catastrophic forgetting

### Key Metrics: 91% accuracy on non-stationary streams
### Resume Bullet: Engineered online learning system with concept drift detection using Hoeffding Trees + ADWIN, maintaining 91% accuracy on non-stationary streams

---

## PROJECT 14: Interpretable ML with Generalized Additive Models (GAMs)

**🎯 The Hook:** Built interpretable regression using GAMs achieving 93% R² on medical risk prediction, with clinically validated shape functions — enabling regulatory compliance and trust.

**Difficulty:** ██████░░░░ (6/10)

### 🧠 Why S-Tier?
- Interpretable ML (critical for healthcare, finance)
- GAMs balance accuracy and interpretability
- Shape functions reveal non-linear relationships
- Regulatory compliance (explainable models)

### Key Metrics: 93% R², clinically validated shape functions
### Resume Bullet: Developed interpretable medical risk prediction using GAMs achieving 93% R² with clinically validated shape functions

---

## PROJECT 15: Multi-Task Learning for Joint Prediction of Related Outcomes

**🎯 The Hook:** Built multi-task deep learning model predicting 5 related medical outcomes simultaneously, achieving 8% accuracy improvement via shared representations and uncertainty-weighted loss.

**Difficulty:** ███████░░░ (7/10)

### 🧠 Why S-Tier?
- Multi-task learning with positive transfer
- Shared vs task-specific layers architecture
- Uncertainty weighting for gradient balancing
- Joint optimization across correlated tasks

### Key Metrics: 8% average accuracy improvement over single-task models
### Resume Bullet: Designed multi-task deep learning for joint prediction of 5 medical outcomes, achieving 8% accuracy improvement via shared representations and uncertainty-weighted loss

---

> **END OF SECTION 1: MACHINE LEARNING**
> See `02_AIML_ENGINEERING.md` for the next 15 projects.
