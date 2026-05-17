import pandas as pd
from filters import flag_jobs

jobs = pd.DataFrame([
    {"title": "Software Engineer Intern",    "company": "Google",  "job_url": "http://a.com/1"},
    {"title": "Senior Software Engineer",    "company": "Meta",    "job_url": "http://a.com/2"},
    {"title": "Junior Backend Developer",    "company": "Shopify", "job_url": "http://a.com/3"},
    {"title": "Data Scientist",              "company": "Amazon",  "job_url": "http://a.com/4"},
    {"title": "",                            "company": "Unknown", "job_url": "http://a.com/5"},
    {"title": "Software Engineering Intern", "company": "Apple",   "job_url": "http://a.com/6"},
])

result = flag_jobs(jobs, "software engineer intern")
for _, r in result.iterrows():
    flag = r["flagged_reason"] or "CLEAN"
    title = str(r["title"])[:40]
    print(f"{title:<42} -> {flag}")
