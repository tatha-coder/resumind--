import os
import random
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT_DIR / "dataset"
DATASET_DIR.mkdir(parents=True, exist_ok=True)

# Also support legacy training/datasets location
LEGACY_DIR = ROOT_DIR / "training" / "datasets"
LEGACY_DIR.mkdir(parents=True, exist_ok=True)

TARGET_SKILLS = [
    "Python", "Java", "C++", "JavaScript", "TypeScript",
    "React", "Node.js", "SQL", "Docker", "AWS",
    "Machine Learning", "Git", "HTML", "CSS", "Excel", "FastAPI"
]

RESUME_SAMPLES = [
    # Full-Stack & Web
    ("Full-stack engineer with 4 years experience building web apps using React, TypeScript, Node.js, and PostgreSQL. Integrated REST APIs and automated Docker deployments.",
     ["React", "TypeScript", "Node.js", "SQL", "Docker", "Git", "JavaScript"]),
    ("Front-end developer skilled in HTML, CSS, JavaScript, and React. Created responsive UI designs and optimized page performance with Git version control.",
     ["HTML", "CSS", "JavaScript", "React", "Git"]),
    ("Software engineer experienced in Python, FastAPI, and PostgreSQL. Built scalable microservices, containerized with Docker, and deployed on AWS EC2.",
     ["Python", "FastAPI", "SQL", "Docker", "AWS", "Git"]),
    ("Web developer proficient in HTML, CSS, JavaScript, Node.js, and Express. Designed interactive user portals with MySQL database integration.",
     ["HTML", "CSS", "JavaScript", "Node.js", "SQL", "Git"]),
    ("Backend developer with expertise in Java, Spring Boot, MySQL, and Docker. Implemented authentication systems and distributed caching on AWS.",
     ["Java", "SQL", "Docker", "AWS", "Git"]),
    ("Senior JavaScript developer specializing in TypeScript, React, Next.js, and CSS styling. Managed Git repositories and CI/CD pipelines.",
     ["JavaScript", "TypeScript", "React", "CSS", "Git", "HTML"]),

    # Data Science & Machine Learning
    ("Data scientist with strong foundation in Python, Machine Learning, SQL, and Excel. Built predictive models using Scikit-Learn and automated data pipelines.",
     ["Python", "Machine Learning", "SQL", "Excel", "Git"]),
    ("Machine Learning engineer proficient in Python, PyTorch, Docker, and AWS. Deployed computer vision and NLP models into production using FastAPI.",
     ["Python", "Machine Learning", "Docker", "AWS", "FastAPI", "Git"]),
    ("Data analyst experienced in SQL querying, Excel dashboards, Python data wrangling, and PowerBI business intelligence reporting.",
     ["SQL", "Excel", "Python"]),
    ("AI researcher with focus on Deep Learning, Machine Learning algorithms, Python, and C++ for high performance computing.",
     ["Machine Learning", "Python", "C++", "Git"]),
    ("Quantitative analyst using Python, Excel, and SQL for statistical modelling and risk assessment.",
     ["Python", "Excel", "SQL"]),

    # Systems, Cloud & DevOps
    ("DevOps engineer with 3+ years managing AWS infrastructure, Docker containerization, CI/CD pipelines with Git, and Python automation scripts.",
     ["AWS", "Docker", "Git", "Python"]),
    ("Cloud architect experienced in AWS services, Docker containers, Kubernetes, and backend microservices written in Java and Python.",
     ["AWS", "Docker", "Java", "Python", "Git"]),
    ("Systems programmer with strong C++, Python, and Linux kernel fundamentals. Developed multithreaded networking utilities using Git.",
     ["C++", "Python", "Git"]),
    ("Software developer experienced in C++, Java, and algorithms. Built desktop simulation tools with SQL storage.",
     ["C++", "Java", "SQL", "Git"]),

    # Enterprise & General Software
    ("Java software engineer with 5 years in enterprise applications, Oracle SQL, Docker containers, and Git collaboration.",
     ["Java", "SQL", "Docker", "Git"]),
    ("Python developer skilled in FastAPI, SQL databases, Docker, and HTML/CSS web interfaces.",
     ["Python", "FastAPI", "SQL", "Docker", "HTML", "CSS", "Git"]),
    ("Junior software engineer with academic background in Python, Java, C++, and SQL databases.",
     ["Python", "Java", "C++", "SQL", "Git"]),
    ("Technical consultant specializing in SQL data migration, Excel reporting, and Python automation.",
     ["SQL", "Excel", "Python"]),
    ("Full-stack developer building APIs in Node.js, frontends in React and TypeScript, with Docker and Git.",
     ["Node.js", "React", "TypeScript", "JavaScript", "Docker", "Git"]),

    # Non-IT & Baseline Negative Samples
    ("Experienced executive assistant managing office scheduling, calendar invites, and basic spreadsheet records.", ["Excel"]),
    ("Sales representative with track record in client acquisition, cold outreach, and customer relationship management.", []),
    ("Customer support specialist handling live inquiries, dispute resolution, and phone communications.", []),
    ("Human resources coordinator managing recruitment pipelines, employee onboarding, and compliance.", []),
    ("Retail store manager overseeing product inventory, employee shifts, and customer satisfaction.", []),
    ("Account manager maintaining client partnerships, contract negotiations, and quarterly business reviews.", []),
    ("Hospitality supervisor managing guest reservations, front-desk staffing, and event coordination.", []),
    ("Operations coordinator tracking shipping logistics, vendor communications, and billing invoices.", ["Excel"]),
    ("Digital marketing specialist managing social media ad spend, SEO copywriting, and brand awareness.", []),
    ("Financial clerk reconciling invoices, bank transactions, and ledger entries using spreadsheets.", ["Excel"])
]


def generate_resume_dataset():
    rows = []
    for text, skills in RESUME_SAMPLES:
        row = {"resume_text": text}
        for skill in TARGET_SKILLS:
            row[skill] = int(skill in skills)
        rows.append(row)

    templates = [
        "Proven background in {s1} and {s2}. Successfully delivered projects involving {s3} and {s4} using Git.",
        "Experienced professional skilled in {s1}, {s2}, and {s3}. Handled database queries in {s4} and deployed via {s5}.",
        "Demonstrated competency in {s1} programming, {s2} frameworks, and {s3} cloud services with strong teamwork.",
        "Passionate engineer with practical experience in {s1}, {s2}, and {s3}. Built automation tools using {s4}.",
        "Technical specialist proficient in {s1} and {s2}. Assisted team with {s3} integration and code reviews using Git."
    ]

    tech_pool = ["Python", "Java", "JavaScript", "TypeScript", "React", "Node.js", "SQL", "Docker", "AWS", "FastAPI", "C++", "Machine Learning"]

    random.seed(42)
    for _ in range(90):
        picked = random.sample(tech_pool, k=random.randint(3, 5))
        template = random.choice(templates)
        args = {f"s{i+1}": picked[i] for i in range(len(picked))}
        for i in range(len(picked), 5):
            args[f"s{i+1}"] = random.choice(tech_pool)
            
        text = template.format(**args)
        if "Git" in text and "Git" not in picked:
            picked.append("Git")

        row = {"resume_text": text}
        for skill in TARGET_SKILLS:
            row[skill] = int(skill in picked)
        rows.append(row)

    return pd.DataFrame(rows)


JOB_DESCRIPTION_SAMPLES = [
    {
        "job_title": "Full-Stack Python & React Developer",
        "job_description": "We are seeking a Full-Stack Engineer with solid experience in Python, FastAPI, React, TypeScript, and Docker. Responsibilities include building REST APIs, managing SQL databases, and deploying microservices on AWS.",
        "required_skills": "Python, FastAPI, React, TypeScript, Docker, SQL, AWS, Git",
        "min_experience_years": 3
    },
    {
        "job_title": "Senior Frontend Engineer",
        "job_description": "Looking for a Frontend Specialist skilled in JavaScript, TypeScript, React, HTML, and modern CSS. Must have experience with Git workflows and responsive component design.",
        "required_skills": "JavaScript, TypeScript, React, HTML, CSS, Git",
        "min_experience_years": 4
    },
    {
        "job_title": "Backend Java Engineer",
        "job_description": "Hiring a Backend Engineer proficient in Java, Spring Boot, SQL, and Docker containerization. Experience with AWS cloud infrastructure and microservice architecture is highly preferred.",
        "required_skills": "Java, SQL, Docker, AWS, Git",
        "min_experience_years": 3
    },
    {
        "job_title": "Machine Learning Engineer",
        "job_description": "Seeking an ML Engineer with deep expertise in Python, Machine Learning algorithms, and PyTorch. Responsible for deploying models with FastAPI and Docker into AWS production environments.",
        "required_skills": "Python, Machine Learning, Docker, AWS, FastAPI, Git",
        "min_experience_years": 2
    },
    {
        "job_title": "Cloud DevOps Engineer",
        "job_description": "Seeking a Cloud Engineer with extensive background in AWS, Docker, Kubernetes, CI/CD with Git, and scripting in Python for infrastructure automation.",
        "required_skills": "AWS, Docker, Git, Python",
        "min_experience_years": 3
    },
    {
        "job_title": "Data Analyst",
        "job_description": "Join our analytics team. You will write complex SQL queries, build executive Excel reports, and create automated data processing workflows using Python.",
        "required_skills": "SQL, Excel, Python",
        "min_experience_years": 1
    },
    {
        "job_title": "C++ Systems Software Developer",
        "job_description": "We need a C++ Systems Developer with strong understanding of data structures, multithreading, and low-level optimization. Git collaboration required.",
        "required_skills": "C++, Git, Python",
        "min_experience_years": 2
    },
    {
        "job_title": "Office Administrator & Coordinator",
        "job_description": "Seeking an Office Administrator to manage office scheduling, billing spreadsheets in Excel, vendor communication, and day-to-day administrative operations.",
        "required_skills": "Excel",
        "min_experience_years": 1
    }
]


def generate_matching_dataset(df_resumes):
    pairs = []
    random.seed(101)

    for _, res_row in df_resumes.iterrows():
        res_text = res_row["resume_text"]
        res_skills = set(s for s in TARGET_SKILLS if res_row[s] == 1)

        for jd in JOB_DESCRIPTION_SAMPLES:
            jd_text = jd["job_description"]
            jd_skills = set(s.strip() for s in jd["required_skills"].split(","))

            if jd_skills:
                overlap = len(res_skills.intersection(jd_skills))
                skill_score = (overlap / len(jd_skills)) * 80.0
            else:
                skill_score = 50.0

            noise = random.uniform(-3.0, 3.0)
            final_score = max(5.0, min(98.0, skill_score + 10.0 + noise))

            pairs.append({
                "job_title": jd["job_title"],
                "resume_text": res_text,
                "job_description": jd_text,
                "target_skills": jd["required_skills"],
                "match_score": round(final_score, 2),
                "is_match": int(final_score >= 60.0)
            })

    random.shuffle(pairs)
    return pd.DataFrame(pairs)


def main():
    print("Generating comprehensive resume training dataset...")
    df_resumes = generate_resume_dataset()

    # Split into train and validation sets (80 / 20)
    df_train, df_val = train_test_split(df_resumes, test_size=0.20, random_state=42)

    # Save to dataset/
    df_resumes.to_csv(DATASET_DIR / "resumes.csv", index=False, encoding="utf-8")
    df_train.to_csv(DATASET_DIR / "skills_train.csv", index=False, encoding="utf-8")
    df_val.to_csv(DATASET_DIR / "skills_validation.csv", index=False, encoding="utf-8")

    # Mirror to legacy location
    df_resumes.to_csv(LEGACY_DIR / "resumes.csv", index=False, encoding="utf-8")

    print(f" Saved {len(df_resumes)} resumes to: {DATASET_DIR / 'resumes.csv'}")
    print(f" Saved {len(df_train)} train resumes to: {DATASET_DIR / 'skills_train.csv'}")
    print(f" Saved {len(df_val)} val resumes to: {DATASET_DIR / 'skills_validation.csv'}")

    print("\nGenerating resume-job matching dataset...")
    df_matches = generate_matching_dataset(df_resumes)
    df_matches.to_csv(DATASET_DIR / "job_description.csv", index=False, encoding="utf-8")
    df_matches.to_csv(LEGACY_DIR / "job_description.csv", index=False, encoding="utf-8")
    print(f" Saved {len(df_matches)} paired match records to: {DATASET_DIR / 'job_description.csv'}")

    print("\nDataset preparation completed successfully!")


if __name__ == "__main__":
    main()
