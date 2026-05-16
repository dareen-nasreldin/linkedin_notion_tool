import os
import json
import anthropic


def filter_jobs(jobs: list[dict], keyword: str) -> list[dict]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or not jobs:
        return [{"job": j, "decision": "keep", "reason": None} for j in jobs]

    client = anthropic.Anthropic(api_key=api_key)

    jobs_json = json.dumps(
        [{"index": i, "title": j["title"], "company": j["company"]} for i, j in enumerate(jobs)],
        indent=2,
    )

    prompt = f"""You are a job listing filter. Classify each job as "keep" or "filter".

Search context:
- Search term: "{keyword}"

Filter rules:
1. RECRUITER_SPAM: Posted by a staffing/recruiting agency or has a vague company name (e.g. "Confidential", "Various Clients", names ending in "Staffing", "Recruiting", "Solutions Inc", "HR Partners", "Talent Group")
2. SENIORITY_MISMATCH: Search contains "intern", "junior", or "entry" but job title is Senior/Lead/Principal/Director/Manager/Head/VP level
3. DUPLICATE: Same title+company appears more than once in this list

Jobs:
{jobs_json}

Return ONLY a JSON array with no extra text or markdown:
[{{"index": 0, "decision": "keep", "reason": null}}, {{"index": 1, "decision": "filter", "reason": "RECRUITER_SPAM"}}]"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        classifications = json.loads(raw.strip())
        result = []
        for cls in classifications:
            idx = cls["index"]
            if idx < len(jobs):
                result.append(
                    {"job": jobs[idx], "decision": cls["decision"], "reason": cls.get("reason")}
                )
        return result
    except Exception:
        return [{"job": j, "decision": "keep", "reason": None} for j in jobs]
