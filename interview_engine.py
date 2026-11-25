"""
Resumind AI - Interview Prep & Assessment Engine
Generates dynamic, skill-calibrated mock interview tests based on candidate resumes.
100% self-contained and local.
"""

import random
from typing import List, Dict, Any, Optional
from io import BytesIO


# =======================================================================
# COMPREHENSIVE CURATED INTERVIEW QUESTION BANK (IT & NON-IT)
# =======================================================================

QUESTION_BANK: List[Dict[str, Any]] = [
    # ------------------- PYTHON & BACKEND -------------------
    {
        "id": "py-01",
        "skill": "Python",
        "category": "IT & SOFTWARE",
        "difficulty": "Intermediate",
        "question": "In Python, how does the Global Interpreter Lock (GIL) affect multi-threaded programs?",
        "options": [
            "It allows multiple CPU-bound threads to execute Python bytecode in parallel across multiple CPU cores.",
            "It prevents multiple threads from executing Python bytecode simultaneously, making multi-threading ineffective for CPU-bound tasks.",
            "It automatically converts multi-threaded code into asynchronous event-loop coroutines.",
            "It isolates memory per thread to eliminate race conditions without developer intervention."
        ],
        "correct_idx": 1,
        "explanation": "The GIL ensures that only one native thread executes Python bytecode at any given moment. For I/O-bound tasks, threads release the GIL during waiting, but for CPU-bound tasks, multiprocessing or C-extensions are required to achieve true multi-core parallelism.",
        "insight": "Interviewers use this to see if you understand Python's concurrency model (GIL vs multiprocessing vs asyncio)."
    },
    {
        "id": "py-02",
        "skill": "Python",
        "category": "IT & SOFTWARE",
        "difficulty": "Intermediate",
        "question": "What is the primary difference between a Python generator (using 'yield') and a standard list comprehension?",
        "options": [
            "Generators store all items in RAM immediately, whereas list comprehensions compute items on demand.",
            "Generators return an iterator that lazily generates items one by one, saving memory for large sequences.",
            "Generators can only produce integers, whereas list comprehensions support arbitrary objects.",
            "List comprehensions are evaluated in background worker threads, whereas generators run on the main thread."
        ],
        "correct_idx": 1,
        "explanation": "Generators compute values on-the-fly (lazy evaluation) and maintain their state between yield statements, which significantly reduces memory consumption compared to eagerly evaluated lists.",
        "insight": "Demonstrates memory-efficient programming and comprehension of iterators."
    },
    {
        "id": "fastapi-01",
        "skill": "FastAPI",
        "category": "IT & SOFTWARE",
        "difficulty": "Intermediate",
        "question": "In FastAPI, what is the primary benefit of using 'Depends()' in route parameters?",
        "options": [
            "It enforces strict database table constraints at the SQLite driver level.",
            "It provides powerful Dependency Injection for sharing database sessions, authentication, and security logic cleanly across endpoints.",
            "It caches HTTP responses in Redis automatically without writing cache keys.",
            "It forces synchronous CPU execution to prevent thread starvation."
        ],
        "correct_idx": 1,
        "explanation": "FastAPI's dependency injection system (`Depends`) allows code reuse, clean separation of concerns (e.g. database sessions, JWT verification), and simplifies unit testing via dependency overrides.",
        "insight": "Evaluates clean API architecture and adherence to modern Python web practices."
    },
    {
        "id": "java-01",
        "skill": "Java",
        "category": "IT & SOFTWARE",
        "difficulty": "Intermediate",
        "question": "In Java, what is the primary difference between 'String', 'StringBuilder', and 'StringBuffer'?",
        "options": [
            "String is immutable; StringBuilder is mutable and not thread-safe; StringBuffer is mutable and thread-safe (synchronized).",
            "String is stored on the stack; StringBuilder and StringBuffer are stored exclusively in L1 CPU cache.",
            "StringBuffer cannot be used in multithreaded environments; StringBuilder is synchronized by default.",
            "String cannot be converted to byte arrays; StringBuilder does not support loops."
        ],
        "correct_idx": 0,
        "explanation": "String objects in Java are immutable. StringBuilder offers maximum performance for single-threaded string concatenation, while StringBuffer provides synchronized thread safety at the expense of locking overhead.",
        "insight": "Core Java memory and thread-safety interview baseline."
    },
    {
        "id": "cpp-01",
        "skill": "C++",
        "category": "IT & SOFTWARE",
        "difficulty": "Advanced",
        "question": "In modern C++ (C++11 and later), what does RAII (Resource Acquisition Is Initialization) ensure?",
        "options": [
            "That variables are initialized to zero at compile-time.",
            "That resources (heap memory, file handles, socket descriptors) are tied to object lifetime and automatically released in destructors upon leaving scope.",
            "That garbage collection runs asynchronously in background POSIX threads.",
            "That all pointers are automatically converted to raw void pointers."
        ],
        "correct_idx": 1,
        "explanation": "RAII ties resource lifecycle to object scope. When smart pointers (`std::unique_ptr`, `std::shared_ptr`) or file streams leave scope, their destructors guarantee exception-safe cleanup without manual deletes.",
        "insight": "The cornerstone idiom of modern production C++ development."
    },
    {
        "id": "ts-01",
        "skill": "TypeScript",
        "category": "IT & SOFTWARE",
        "difficulty": "Intermediate",
        "question": "What is the key difference between a TypeScript 'interface' and a 'type' alias?",
        "options": [
            "Interfaces can be declaration-merged by defining them multiple times; type aliases cannot be reopened once declared.",
            "Interfaces only exist at runtime in browser JS; types exist only inside Node.js modules.",
            "Type aliases can only represent primitive numbers; interfaces represent functions only.",
            "Interfaces require compilation to WebAssembly binaries."
        ],
        "correct_idx": 0,
        "explanation": "TypeScript interfaces support declaration merging (ideal for library authors and extending schemas), whereas type aliases can express union types, primitives, and tuples directly.",
        "insight": "Differentiates casual TypeScript users from senior architecture engineers."
    },
    {
        "id": "node-01",
        "skill": "Node.js",
        "category": "IT & SOFTWARE",
        "difficulty": "Intermediate",
        "question": "In Node.js, what is the danger of executing intensive synchronous CPU loops (e.g. `JSON.parse` of a 500MB string) on the main thread?",
        "options": [
            "It deletes the `package.json` lockfile automatically.",
            "It blocks the single-threaded Event Loop, preventing all other concurrent HTTP incoming requests from being processed until the loop completes.",
            "It forces Node.js to spin up 100 new worker OS processes.",
            "It terminates the underlying V8 garbage collector permanently."
        ],
        "correct_idx": 1,
        "explanation": "Node.js handles concurrency using a single main event loop thread. Long CPU-bound operations stall the entire server for all connected clients. Worker threads or microservices should be used instead.",
        "insight": "Core Node.js scalability and non-blocking I/O concept."
    },

    # ------------------- DATA SCIENCE, ML & PYTORCH -------------------
    {
        "id": "ml-01",
        "skill": "Machine Learning",
        "category": "DATA SCIENCE & AI",
        "difficulty": "Intermediate",
        "question": "When training a classification model on an imbalanced dataset (e.g., 98% negative, 2% positive), which metric is the LEAST reliable indicator of performance?",
        "options": [
            "Precision-Recall AUC (PR-AUC)",
            "Overall Accuracy",
            "F1-Score",
            "Balanced Accuracy"
        ],
        "correct_idx": 1,
        "explanation": "A dummy classifier that predicts 'negative' for 100% of samples achieves 98% raw accuracy while completely failing to detect the minority class. PR-AUC and F1-score provide much more meaningful evaluations.",
        "insight": "Tests practical ML experience over textbook memorization."
    },
    {
        "id": "torch-01",
        "skill": "PyTorch",
        "category": "DATA SCIENCE & AI",
        "difficulty": "Intermediate",
        "question": "In PyTorch, why must you call 'optimizer.zero_grad()' before 'loss.backward()' during standard training loops?",
        "options": [
            "Because PyTorch initializes gradients with random Gaussian noise on every backward pass.",
            "Because PyTorch accumulates (sums) gradients into `.grad` by default, leading to incorrect updates if not reset.",
            "Because calling zero_grad() flushes the GPU memory cache to prevent Out-Of-Memory (OOM) errors.",
            "Because PyTorch cannot compute matrix dot products without clearing previous weights."
        ],
        "correct_idx": 1,
        "explanation": "PyTorch accumulates gradients across consecutive `backward()` calls (useful for recurrent networks or simulating larger batch sizes). If not reset with `optimizer.zero_grad()`, gradients from previous iterations corrupt the current step.",
        "insight": "A classic deep learning interview checkpoint for PyTorch developers."
    },
    {
        "id": "ai-01",
        "skill": "Artificial Intelligence",
        "category": "DATA SCIENCE & AI",
        "difficulty": "Advanced",
        "question": "What is the primary difference between Fine-Tuning a Large Language Model (LLM) and using Retrieval-Augmented Generation (RAG)?",
        "options": [
            "Fine-Tuning adapts model weights for specific style/tone/tasks; RAG retrieves up-to-date factual documents dynamically at inference time without altering model weights.",
            "RAG requires retraining all billions of parameters, whereas fine-tuning only edits the prompt string.",
            "Fine-Tuning completely eliminates hallucinations, while RAG does not support source citations.",
            "RAG only works with vector graphics, whereas fine-tuning works with text."
        ],
        "correct_idx": 0,
        "explanation": "RAG supplies grounded, real-time external knowledge in the prompt context to prevent hallucinations and access proprietary data without training. Fine-tuning adjusts model parameters to learn specialized syntax, behaviors, or domain dialects.",
        "insight": "Critical modern AI engineering knowledge for GenAI roles."
    },

    # ------------------- DATABASE & SQL -------------------
    {
        "id": "sql-01",
        "skill": "SQL",
        "category": "DATABASE",
        "difficulty": "Intermediate",
        "question": "What is the difference between an INNER JOIN and a LEFT JOIN in SQL?",
        "options": [
            "INNER JOIN returns all rows from the left table; LEFT JOIN returns only rows where both tables match.",
            "INNER JOIN returns only rows with matching values in both tables; LEFT JOIN returns all rows from the left table plus matching rows from the right table.",
            "INNER JOIN modifies table schemas; LEFT JOIN only executes read-only queries.",
            "INNER JOIN is non-deterministic; LEFT JOIN guarantees sorted results."
        ],
        "correct_idx": 1,
        "explanation": "INNER JOIN filters out rows that do not have a counterpart in the joined table. LEFT JOIN preserves all rows from the primary (left) table, populating NULL for missing right-table columns.",
        "insight": "Fundamental database competency required across almost all tech positions."
    },
    {
        "id": "db-01",
        "skill": "SQL",
        "category": "DATABASE",
        "difficulty": "Advanced",
        "question": "What is the primary trade-off of adding multiple indexes to a relational database table?",
        "options": [
            "Speeds up SELECT queries, but increases disk space and slows down INSERT, UPDATE, and DELETE operations.",
            "Prevents deadlock errors, but reduces query execution speed across all transactions.",
            "Allows unlimited table size, but disables foreign key constraints.",
            "Guarantees ACID transactions, but causes tables to fragment into separate databases."
        ],
        "correct_idx": 0,
        "explanation": "Indexes (like B-trees) create fast lookup structures that dramatically accelerate search queries, but each write operation (INSERT/UPDATE/DELETE) must maintain and rebalance those index trees.",
        "insight": "Tests database optimization and architectural trade-off reasoning."
    },
    {
        "id": "nosql-01",
        "skill": "MongoDB",
        "category": "DATABASE",
        "difficulty": "Intermediate",
        "question": "When would a NoSQL document database (like MongoDB) be preferred over a traditional relational database (like PostgreSQL)?",
        "options": [
            "When strict multi-table ACID transactions and financial ledger auditing are the highest priority.",
            "When dealing with rapidly evolving schema requirements, hierarchical/nested document data, and horizontal scale-out workloads.",
            "When the dataset strictly consists of normalized tabular data with complex multi-table joins.",
            "When queries are exclusively executed using standard ANSI SQL syntax."
        ],
        "correct_idx": 1,
        "explanation": "Document databases excel when data naturally forms nested objects (e.g. user profiles with varying fields) and when horizontal sharding across distributed clusters is needed.",
        "insight": "Reveals whether you select tools based on architecture rather than hype."
    },

    # ------------------- CLOUD & DEVOPS -------------------
    {
        "id": "docker-01",
        "skill": "Docker",
        "category": "CLOUD & DEVOPS",
        "difficulty": "Intermediate",
        "question": "How does a Docker container differ fundamentally from a Virtual Machine (VM)?",
        "options": [
            "Containers virtualize hardware and run complete separate guest operating system kernels.",
            "Containers share the host OS kernel and isolate user spaces via namespaces and cgroups, making them lightweight and fast.",
            "Containers can only run on Linux, while Virtual Machines can run on any device.",
            "Containers require dedicated hypervisor software like ESXi or Hyper-V."
        ],
        "correct_idx": 1,
        "explanation": "VMs duplicate entire guest OS kernels on top of a hypervisor. Containers share the host kernel, which drastically reduces memory footprint and boot times (milliseconds vs minutes).",
        "insight": "Core DevOps conceptual test for infrastructure, cloud, and backend roles."
    },
    {
        "id": "git-01",
        "skill": "Git",
        "category": "CLOUD & DEVOPS",
        "difficulty": "Intermediate",
        "question": "What is the difference between 'git merge' and 'git rebase' when integrating a feature branch into main?",
        "options": [
            "Merge creates a 3-way merge commit preserving exact chronological branch history; Rebase replays commits on top of main for a linear commit history.",
            "Merge deletes the feature branch commits; Rebase keeps both branches permanently locked.",
            "Merge only works for local commits; Rebase is required for pushing to GitHub.",
            "Rebase is always non-destructive and cannot cause conflicts."
        ],
        "correct_idx": 0,
        "explanation": "Merge preserves exact historical branching context with a dedicated merge commit. Rebase rewrites commit hashes to place feature work cleanly at the tip of the target branch.",
        "insight": "Shows team collaboration maturity and Git workflow understanding."
    },
    {
        "id": "k8s-01",
        "skill": "Kubernetes",
        "category": "CLOUD & DEVOPS",
        "difficulty": "Advanced",
        "question": "In Kubernetes, what is the smallest deployable computing unit that can be created and managed?",
        "options": [
            "A Container",
            "A Pod",
            "A Deployment",
            "A ReplicaSet"
        ],
        "correct_idx": 1,
        "explanation": "A Pod encapsulates one or more tightly coupled containers, shared storage volumes, and a unique network IP address within the cluster.",
        "insight": "Basic Kubernetes terminology verification."
    },
    {
        "id": "aws-01",
        "skill": "AWS",
        "category": "CLOUD & DEVOPS",
        "difficulty": "Intermediate",
        "question": "In AWS architecture, what is the difference between Amazon S3 and Amazon EBS?",
        "options": [
            "S3 is scalable object storage accessible over HTTP REST APIs; EBS is persistent block storage attached as virtual drives to EC2 instances.",
            "S3 only stores relational SQL tables; EBS is designed exclusively for serverless Lambda functions.",
            "S3 cannot store files larger than 1MB; EBS stores unlimited files over the public internet.",
            "EBS is open-source software; S3 is a hardware server hosted on-premises."
        ],
        "correct_idx": 0,
        "explanation": "Amazon S3 provides durable global object storage (ideal for backups, static media, data lakes). Amazon EBS provides low-latency block-level volumes mounted directly to EC2 compute nodes.",
        "insight": "Fundamental cloud architecture knowledge check."
    },
    {
        "id": "linux-01",
        "skill": "Linux",
        "category": "CLOUD & DEVOPS",
        "difficulty": "Intermediate",
        "question": "In Linux file permissions, what permissions does the numeric octal mode `755` represent?",
        "options": [
            "Owner: Read/Write/Execute (rwx); Group: Read/Execute (r-x); Others: Read/Execute (r-x)",
            "Owner: Read only (r--); Group: Write only (-w-); Others: Execute only (--x)",
            "All users have full Read, Write, and Execute permissions.",
            "Owner: Read/Write (rw-); Group: Read/Write (rw-); Others: No access (---)"
        ],
        "correct_idx": 0,
        "explanation": "Binary permissions: 4 (read) + 2 (write) + 1 (execute). `7` = rwx (owner), `5` = r-x (group), `5` = r-x (others).",
        "insight": "Every system engineer, DevOps, and backend developer should know standard POSIX permissions."
    },
    {
        "id": "sec-01",
        "skill": "Cybersecurity",
        "category": "CYBERSECURITY & NETWORKING",
        "difficulty": "Intermediate",
        "question": "What is the primary countermeasure to protect a web application against SQL Injection attacks?",
        "options": [
            "Encrypting the client's web browser using HTTPS.",
            "Using Parameterized Queries (Prepared Statements) or an ORM that treats user inputs strictly as parameters rather than executable SQL syntax.",
            "Restricting user passwords to numbers only.",
            "Installing an antivirus program on the database server."
        ],
        "correct_idx": 1,
        "explanation": "Parameterized queries separate the query structure from user-supplied data, ensuring the SQL engine never interprets input characters as SQL commands.",
        "insight": "Critical application security principle across all developer levels."
    },
    {
        "id": "pm-01",
        "skill": "Project Management",
        "category": "MANAGEMENT & ADMINISTRATION",
        "difficulty": "Intermediate",
        "question": "In Agile/Scrum frameworks, what is the primary purpose of the Sprint Retrospective meeting?",
        "options": [
            "To assign blame to developers who did not complete user story points.",
            "To reflect on the past sprint (team dynamics, processes, tools) and agree on continuous process improvements for subsequent sprints.",
            "To demonstrate finished features to external stakeholders and sales prospects.",
            "To negotiate annual developer salaries."
        ],
        "correct_idx": 1,
        "explanation": "The Sprint Review inspects the product increment with stakeholders; the Sprint Retrospective inspects team health, workflows, and process enhancements to drive continuous improvement.",
        "insight": "Demonstrates practical agile maturity and team dynamics literacy."
    },

    # ------------------- JAVASCRIPT & FRONTEND -------------------
    {
        "id": "react-01",
        "skill": "React",
        "category": "IT & SOFTWARE",
        "difficulty": "Intermediate",
        "question": "In React, why should you avoid mutating state directly (e.g. `state.count = 5`) instead of using `setState` or `useState` updater functions?",
        "options": [
            "Because direct mutation throws an immediate JavaScript runtime TypeError.",
            "Because React relies on shallow reference equality checks; direct mutation does not trigger re-rendering of components.",
            "Because direct mutation causes the browser to clear local storage.",
            "Because React converts all state variables into immutable WebAssembly binaries."
        ],
        "correct_idx": 1,
        "explanation": "React checks whether state object references have changed to decide if re-renders are needed. Mutating state directly modifies the existing reference in-place, bypassing React's reactive rendering cycle.",
        "insight": "Differentiates true React developers from casual beginners."
    },
    {
        "id": "js-01",
        "skill": "JavaScript",
        "category": "IT & SOFTWARE",
        "difficulty": "Intermediate",
        "question": "What is the Event Loop in JavaScript responsible for?",
        "options": [
            "Compiling JavaScript into machine assembly code before execution.",
            "Monitoring the Call Stack and Task Queue, pushing queued asynchronous callbacks to the stack when it becomes empty.",
            "Enforcing synchronous multi-threaded execution across multi-core CPUs.",
            "Managing garbage collection cycles in V8."
        ],
        "correct_idx": 1,
        "explanation": "JavaScript is single-threaded. The event loop continuously checks if the call stack is clear, then shifts ready callbacks from the microtask/macrotask queues onto the stack.",
        "insight": "Core JavaScript runtime architecture question."
    },

    # ------------------- BEHAVIORAL & SCENARIO (STAR METHOD) -------------------
    {
        "id": "beh-01",
        "skill": "Problem Solving",
        "category": "BEHAVIORAL & SCENARIOS",
        "difficulty": "Intermediate",
        "question": "Scenario: A high-priority production bug causes intermittent failures for 15% of active users. The root cause is unclear. How should you approach this situation?",
        "options": [
            "Immediately rewrite the entire subsystem from scratch and deploy without unit tests.",
            "Acknowledge the incident, review system logs and error tracking to isolate patterns, deploy a safe rollback or defensive patch, and conduct a blameless post-mortem.",
            "Wait until the scheduled bi-weekly sprint release to investigate the issue.",
            "Blame the junior engineer who pushed the last commit and submit a critical complaint."
        ],
        "correct_idx": 1,
        "explanation": "Top engineering organizations value systematic incident management: prompt triage, telemetry/logging analysis, mitigating user impact first (rollback/flag), followed by blameless root cause analysis.",
        "insight": "Assesses professionalism, calm under pressure, and systematic debugging."
    },
    {
        "id": "beh-02",
        "skill": "Project Management",
        "category": "BEHAVIORAL & SCENARIOS",
        "difficulty": "Intermediate",
        "question": "Scenario: Two days before a critical deadline, a product manager requests three new scope additions. How do you respond?",
        "options": [
            "Accept all requests silently, work 20 hours a day, and sacrifice testing.",
            "Flatly refuse to speak with the product manager until the release is done.",
            "Clarify trade-offs: explain that adding new features now risks release stability, and propose scoping them into an immediate Phase 2 release or swapping existing non-critical items.",
            "Pretend to implement them and release broken code on deadline day."
        ],
        "correct_idx": 2,
        "explanation": "Constructive scope management involves transparent stakeholder communication about trade-offs (Iron Triangle: Scope, Time, Quality) rather than silent overpromising.",
        "insight": "Assesses stakeholder management, realistic prioritization, and project maturity."
    },

    # ------------------- ACCOUNTING & FINANCE -------------------
    {
        "id": "fin-01",
        "skill": "Accounting",
        "category": "ACCOUNTING & FINANCE",
        "difficulty": "Intermediate",
        "question": "What is the Fundamental Accounting Equation that balances every company balance sheet?",
        "options": [
            "Assets = Liabilities + Owner's Equity",
            "Assets = Revenue - Operating Expenses",
            "Equity = Assets + Liabilities",
            "Gross Profit = Net Sales - Retained Earnings"
        ],
        "correct_idx": 0,
        "explanation": "Every double-entry bookkeeping system is founded on Assets = Liabilities + Equity. Every transaction impacts this equation symmetrically.",
        "insight": "Foundational accounting knowledge check."
    },
    {
        "id": "fin-02",
        "skill": "Financial Analysis",
        "category": "ACCOUNTING & FINANCE",
        "difficulty": "Intermediate",
        "question": "What does a high Debt-to-Equity (D/E) ratio indicate about a company's financial structure?",
        "options": [
            "The company is funded primarily through internal retained cash reserves.",
            "The company is aggressively financing growth with debt, which increases financial leverage and bankruptcy risk during downturns.",
            "The company has zero outstanding creditor obligations.",
            "The company's stock price will automatically increase."
        ],
        "correct_idx": 1,
        "explanation": "High D/E signifies high leverage; while it can amplify returns during growth periods, it raises debt service costs and vulnerability to interest rate shifts.",
        "insight": "Financial statement analysis and corporate finance competency."
    },

    # ------------------- SALES & MARKETING -------------------
    {
        "id": "mkt-01",
        "skill": "Digital Marketing",
        "category": "SALES & MARKETING",
        "difficulty": "Intermediate",
        "question": "What is the primary difference between SEO (Search Engine Optimization) and SEM (Search Engine Marketing)?",
        "options": [
            "SEO focuses on organic search visibility through quality content and technical optimization; SEM relies primarily on paid search ads (e.g. Google PPC).",
            "SEO is exclusively for social media platforms like Instagram; SEM is for email newsletters.",
            "SEO delivers immediate traffic on day one, whereas SEM takes 6–12 months to show results.",
            "SEM cannot be measured with conversion analytics, while SEO can."
        ],
        "correct_idx": 0,
        "explanation": "SEO is an organic, long-term compounding strategy. SEM (such as Google Ads pay-per-click) delivers targeted paid placement with immediate visibility for target keywords.",
        "insight": "Marketing channel strategy and acquisition economics."
    },
    {
        "id": "mkt-02",
        "skill": "Sales",
        "category": "SALES & MARKETING",
        "difficulty": "Intermediate",
        "question": "In B2B sales cycles, what does the BANT qualification framework stand for?",
        "options": [
            "Brand, Advertising, Network, Traction",
            "Budget, Authority, Need, Timeline",
            "Backlog, Alignment, Negotiation, Terms",
            "Billing, Acquisition, Net-Retention, Turnover"
        ],
        "correct_idx": 1,
        "explanation": "BANT helps sales teams qualify prospect readiness: Do they have Budget? Does the contact have Authority? Is there a clear business Need? What is their decision Timeline?",
        "insight": "Standard sales pipeline management and qualification rigor."
    },

    # ------------------- HUMAN RESOURCES -------------------
    {
        "id": "hr-01",
        "skill": "Human Resources",
        "category": "HUMAN RESOURCES",
        "difficulty": "Intermediate",
        "question": "What is the primary objective of a 360-degree performance feedback review?",
        "options": [
            "To automatically terminate the bottom 10% of performers without manager input.",
            "To gather holistic performance insights from peers, direct reports, supervisors, and self-evaluation to reduce individual bias.",
            "To publicly post salary numbers and rankings across the company intranet.",
            "To eliminate the need for regular 1-on-1 manager check-ins."
        ],
        "correct_idx": 1,
        "explanation": "360 reviews mitigate single-manager bias by collecting balanced qualitative feedback from multiple organizational angles to guide career growth and objective evaluations.",
        "insight": "Modern HR talent development and appraisal methodologies."
    }
]


# =======================================================================
# INTERVIEW TEST GENERATOR
# =======================================================================

def generate_interview_test(
    candidate_skills: List[str],
    resume_category: Optional[str] = None,
    num_questions: int = 5,
    focus_mode: str = "Balanced Mock Interview"
) -> List[Dict[str, Any]]:
    """
    Selects and calibrates interview questions tailored to the candidate's skills.
    Returns a shuffled list of question objects with randomized option order.
    """
    normalized_candidate_skills = {s.strip().lower() for s in candidate_skills if s}

    matching_questions: List[Dict[str, Any]] = []
    category_questions: List[Dict[str, Any]] = []
    general_questions: List[Dict[str, Any]] = []

    for q in QUESTION_BANK:
        q_skill = q["skill"].lower()
        q_cat = q["category"]

        # Match directly by detected candidate skill
        if q_skill in normalized_candidate_skills:
            matching_questions.append(q)
        elif resume_category and q_cat.upper() in resume_category.upper():
            category_questions.append(q)
        else:
            general_questions.append(q)

    # Balance questions based on focus_mode
    selected: List[Dict[str, Any]] = []

    if focus_mode == "Technical Only":
        tech_pool = [q for q in matching_questions if q["category"] != "BEHAVIORAL & SCENARIOS"]
        random.shuffle(tech_pool)
        selected.extend(tech_pool)
    elif focus_mode == "Behavioral & Leadership":
        beh_pool = [q for q in QUESTION_BANK if q["category"] in ["BEHAVIORAL & SCENARIOS", "HUMAN RESOURCES", "MANAGEMENT & ADMINISTRATION"]]
        random.shuffle(beh_pool)
        selected.extend(beh_pool)
    else:  # Balanced Mock Interview
        random.shuffle(matching_questions)
        selected.extend(matching_questions[:max(2, num_questions - 2)])

        # Ensure at least 1 behavioral / scenario question
        beh_questions = [q for q in QUESTION_BANK if q["category"] == "BEHAVIORAL & SCENARIOS"]
        if beh_questions:
            selected.append(random.choice(beh_questions))

    # Fill remaining quota from category or general pool
    if len(selected) < num_questions:
        remaining_needed = num_questions - len(selected)
        pool = [q for q in (category_questions + general_questions) if q not in selected]
        random.shuffle(pool)
        selected.extend(pool[:remaining_needed])

    # If still not enough, sample from full bank
    if len(selected) < num_questions:
        pool = [q for q in QUESTION_BANK if q not in selected]
        random.shuffle(pool)
        selected.extend(pool[:num_questions - len(selected)])

    # Trim to exact count and prepare with safe randomized options
    final_questions = []
    for idx, raw_q in enumerate(selected[:num_questions]):
        original_options = raw_q["options"]
        correct_text = original_options[raw_q["correct_idx"]]

        # Create a shuffled copy of options
        shuffled_options = list(original_options)
        random.shuffle(shuffled_options)
        new_correct_idx = shuffled_options.index(correct_text)

        final_questions.append({
            "test_id": f"q_{idx+1}",
            "question_number": idx + 1,
            "skill": raw_q["skill"],
            "category": raw_q["category"],
            "difficulty": raw_q["difficulty"],
            "question": raw_q["question"],
            "options": shuffled_options,
            "correct_idx": new_correct_idx,
            "explanation": raw_q["explanation"],
            "insight": raw_q["insight"]
        })

    return final_questions


# =======================================================================
# TEST EVALUATION ENGINE
# =======================================================================

def evaluate_test(questions: List[Dict[str, Any]], user_answers: Dict[str, int]) -> Dict[str, Any]:
    """
    Evaluates the user's answers against the test questions.
    Returns scores, grade, skill breakdown, and personalized review items.
    """
    total = len(questions)
    if total == 0:
        return {"score_pct": 0, "correct_count": 0, "total": 0, "readiness": "N/A", "review": []}

    correct_count = 0
    skill_stats: Dict[str, Dict[str, int]] = {}
    review_items = []

    for q in questions:
        q_id = q["test_id"]
        correct_idx = q["correct_idx"]
        user_choice = user_answers.get(q_id, None)

        is_correct = (user_choice == correct_idx)
        if is_correct:
            correct_count += 1

        # Track per-skill statistics
        skill_name = q["skill"]
        if skill_name not in skill_stats:
            skill_stats[skill_name] = {"total": 0, "correct": 0}
        skill_stats[skill_name]["total"] += 1
        if is_correct:
            skill_stats[skill_name]["correct"] += 1

        review_items.append({
            "question_number": q["question_number"],
            "skill": q["skill"],
            "question": q["question"],
            "options": q["options"],
            "user_choice": user_choice,
            "correct_idx": correct_idx,
            "is_correct": is_correct,
            "user_answer_text": q["options"][user_choice] if user_choice is not None else "No answer submitted",
            "correct_answer_text": q["options"][correct_idx],
            "explanation": q["explanation"],
            "insight": q["insight"]
        })

    score_pct = round((correct_count / total) * 100, 1)

    # Calibrate Interview Readiness Tier
    if score_pct >= 90:
        tier = "Elite Candidate"
        readiness_badge = "🏆 Exceptional Mastery — Ready for Senior / Principal Rounds"
        readiness_color = "#166534"
    elif score_pct >= 75:
        tier = "Strong Hire"
        readiness_badge = "🌟 Strong Hire — Confident Technical & Practical Alignment"
        readiness_color = "#2563EB"
    elif score_pct >= 60:
        tier = "Competent"
        readiness_badge = "👍 Solid Baseline — Targeted polish recommended before interview"
        readiness_color = "#D97706"
    else:
        tier = "Needs Revision"
        readiness_badge = "📚 Needs Targeted Revision — Key conceptual gaps identified"
        readiness_color = "#DC2626"

    # Identify improvement topics
    weak_skills = [
        s for s, stats in skill_stats.items()
        if stats["correct"] < stats["total"]
    ]

    return {
        "score_pct": score_pct,
        "correct_count": correct_count,
        "total": total,
        "tier": tier,
        "readiness_badge": readiness_badge,
        "readiness_color": readiness_color,
        "skill_stats": skill_stats,
        "weak_skills": weak_skills,
        "review": review_items
    }


# =======================================================================
# INTERVIEW REPORT PDF GENERATOR
# =======================================================================

def generate_interview_pdf_report(candidate_name: str, evaluation_result: Dict[str, Any]) -> Optional[bytes]:
    """Generates a downloadable PDF assessment summary using ReportLab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor("#4263EB"),
            spaceAfter=8
        )
        sub_style = ParagraphStyle(
            'SubTitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=16
        )

        story = [
            Paragraph("RESUMIND AI — INTERVIEW READINESS REPORT", title_style),
            Paragraph(f"Candidate: <b>{candidate_name}</b> | Score: <b>{evaluation_result['score_pct']}%</b> ({evaluation_result['correct_count']}/{evaluation_result['total']}) | Status: <b>{evaluation_result['tier']}</b>", sub_style),
            Spacer(1, 10)
        ]

        # Review items table
        table_data = [["#", "Skill", "Result", "Question Preview"]]
        for item in evaluation_result.get("review", []):
            res_str = "CORRECT" if item["is_correct"] else "INCORRECT"
            preview = item["question"][:75] + ("..." if len(item["question"]) > 75 else "")
            table_data.append([
                str(item["question_number"]),
                item["skill"],
                res_str,
                preview
            ])

        t = Table(table_data, colWidths=[25, 100, 75, 320])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(t)
        story.append(Spacer(1, 18))

        # Recommendations
        if evaluation_result.get("weak_skills"):
            story.append(Paragraph("<b>Recommended Areas for Revision:</b>", styles["Heading3"]))
            weak_text = ", ".join(evaluation_result["weak_skills"])
            story.append(Paragraph(f"Focus technical preparation on: {weak_text}", styles["Normal"]))

        doc.build(story)
        return buffer.getvalue()
    except Exception as e:
        print(f"[Notice] Interview PDF generation: {e}")
        return None
