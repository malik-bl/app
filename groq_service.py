import os
import json
from groq import Groq

class GroqService:
    def __init__(self):
        self.client = Groq(api_key=os.environ.get('GROQ_API_KEY', 'your-groq-api-key'))
        self.model = "llama-3.3-70b-versatile"

    def _chat(self, messages, temperature=0.7, max_tokens=2048):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq API error: {e}")
            return None

    def _parse_json(self, text):
        """Robustly extract JSON from LLM response."""
        if not text:
            return None
        text = text.strip()
        # Strip markdown code fences
        if '```' in text:
            for part in text.split('```'):
                part = part.strip()
                if part.startswith('json'):
                    part = part[4:].strip()
                if part.startswith(('{', '[')):
                    text = part
                    break
        try:
            return json.loads(text)
        except Exception:
            return None

    def analyze_cv(self, cv_text: str, field: str) -> dict:
        prompt = f"""Analyze this CV for a {field} position. Return ONLY valid JSON:
{{
  "name": "candidate name",
  "summary": "2-3 sentence professional summary",
  "experience_years": 0,
  "skills": ["skill1", "skill2", "skill3"],
  "strengths": ["strength1", "strength2", "strength3"],
  "gaps": ["gap1", "gap2", "gap3"],
  "education": "highest education",
  "experience_level": "Junior/Mid/Senior",
  "overall_score": 75,
  "field_match": 80
}}

CV TEXT:
{cv_text[:3000]}"""
        result = self._chat([{"role": "user", "content": prompt}], temperature=0.3)
        parsed = self._parse_json(result)
        if parsed and isinstance(parsed, dict):
            return parsed
        return {
            "name": "Candidate", "summary": "Experienced professional",
            "experience_years": 2, "skills": ["Communication", "Problem Solving"],
            "strengths": ["Adaptable", "Quick learner"],
            "gaps": ["Leadership experience", "Advanced certifications"],
            "education": "Bachelor's Degree", "experience_level": "Mid",
            "overall_score": 70, "field_match": 65
        }

    def generate_questions(self, cv_text: str, cv_analysis: dict, field: str) -> list:
        skills = cv_analysis.get('skills', [])
        gaps   = cv_analysis.get('gaps', [])
        level  = cv_analysis.get('experience_level', 'Mid')
        prompt = f"""Generate exactly 7 interview questions for a {level} {field} candidate.
CV Skills: {', '.join(skills[:5])}
Skill Gaps: {', '.join(gaps[:3])}
Return ONLY a JSON array:
[
  {{
    "id": 1,
    "question": "Question text here?",
    "category": "Technical/Behavioral/Situational",
    "difficulty": "Easy/Medium/Hard",
    "expected_keywords": ["keyword1", "keyword2"],
    "time_limit": 120
  }}
]
Mix: 3 technical, 2 behavioral, 2 situational. Make them specific to {field}."""
        result = self._chat([{"role": "user", "content": prompt}], temperature=0.6)
        parsed = self._parse_json(result)
        if parsed and isinstance(parsed, list) and len(parsed) > 0:
            return parsed
        return [
            {"id":1,"question":f"Tell me about your experience in {field}?","category":"Behavioral","difficulty":"Easy","expected_keywords":["experience","projects"],"time_limit":120},
            {"id":2,"question":f"What are your strongest technical skills in {field}?","category":"Technical","difficulty":"Medium","expected_keywords":["skills","tools"],"time_limit":120},
            {"id":3,"question":"Describe a challenging project and how you handled it?","category":"Behavioral","difficulty":"Medium","expected_keywords":["challenge","solution","result"],"time_limit":150},
            {"id":4,"question":"How do you stay updated with the latest trends in your field?","category":"Behavioral","difficulty":"Easy","expected_keywords":["learning","courses","community"],"time_limit":90},
            {"id":5,"question":f"Walk me through a technical problem you solved recently in {field}?","category":"Technical","difficulty":"Hard","expected_keywords":["problem","approach","solution"],"time_limit":180},
            {"id":6,"question":"How do you handle tight deadlines and pressure?","category":"Situational","difficulty":"Medium","expected_keywords":["prioritize","manage","communicate"],"time_limit":120},
            {"id":7,"question":"Where do you see yourself in 3-5 years?","category":"Behavioral","difficulty":"Easy","expected_keywords":["growth","goals","skills"],"time_limit":90}
        ]

    def analyze_answer(self, question: dict, answer: str, field: str, cv_analysis: dict) -> dict:
        if not answer.strip():
            return {
                "score":0,"clarity":0,"relevance":0,"confidence":0,
                "feedback":"No answer provided.",
                "missing_points":question.get('expected_keywords',[]),
                "strengths":[],"improvements":["Please provide an answer to the question."]
            }
        prompt = f"""Evaluate this interview answer for a {field} position.
Question: {question.get('question')}
Category: {question.get('category')}
Expected Keywords: {', '.join(question.get('expected_keywords', []))}
Answer: {answer}
Return ONLY valid JSON:
{{
  "score": 75, "clarity": 80, "relevance": 70, "confidence": 75,
  "feedback": "Overall feedback in 2-3 sentences",
  "missing_points": ["point1"], "strengths": ["strength1"],
  "improvements": ["improvement1"]
}}
Score each metric 0-100."""
        result = self._chat([{"role": "user", "content": prompt}], temperature=0.4)
        parsed = self._parse_json(result)
        if parsed and isinstance(parsed, dict):
            return parsed
        return {
            "score":65,"clarity":70,"relevance":65,"confidence":60,
            "feedback":"The answer addressed the question but could be more structured.",
            "missing_points":question.get('expected_keywords',[])[:2],
            "strengths":["Relevant experience mentioned"],
            "improvements":["Use STAR method","Be more specific with examples"]
        }

    def generate_final_feedback(self, answers: list, cv_analysis: dict, field: str) -> dict:
        scores = [a.get('answer_analysis', {}).get('score', 0) for a in answers]
        avg_score = sum(scores) / len(scores) if scores else 0
        all_improvements, all_strengths = [], []
        for a in answers:
            analysis = a.get('answer_analysis', {})
            all_improvements.extend(analysis.get('improvements', []))
            all_strengths.extend(analysis.get('strengths', []))

        prompt = f"""Generate final interview feedback for a {field} candidate.
Overall Score: {avg_score:.0f}/100
CV Gaps: {', '.join(cv_analysis.get('gaps', []))}
Common Improvements Needed: {', '.join(list(set(all_improvements))[:5])}
Demonstrated Strengths: {', '.join(list(set(all_strengths))[:5])}
Return ONLY valid JSON:
{{
  "overall_score": {avg_score:.0f},
  "grade": "A/B/C/D/F",
  "hire_recommendation": "Strong Yes/Yes/Maybe/No",
  "summary": "3-4 sentence executive summary",
  "top_strengths": ["strength1", "strength2", "strength3"],
  "critical_gaps": ["gap1", "gap2", "gap3"],
  "communication_score": 75,
  "technical_score": 70,
  "behavioral_score": 80,
  "areas_to_improve": [
    {{"area": "area name", "priority": "High/Medium/Low", "description": "what to improve"}}
  ]
}}"""
        result = self._chat([{"role": "user", "content": prompt}], temperature=0.4)
        parsed = self._parse_json(result)
        if parsed and isinstance(parsed, dict):
            return parsed
        grade = 'A' if avg_score>=90 else 'B' if avg_score>=80 else 'C' if avg_score>=70 else 'D' if avg_score>=60 else 'F'
        return {
            "overall_score": round(avg_score), "grade": grade,
            "hire_recommendation": "Yes" if avg_score>=70 else "Maybe",
            "summary": f"The candidate demonstrated {avg_score:.0f}% proficiency in the {field} interview.",
            "top_strengths": list(set(all_strengths))[:3],
            "critical_gaps": cv_analysis.get('gaps', [])[:3],
            "communication_score": round(avg_score*0.9),
            "technical_score": round(avg_score*1.1),
            "behavioral_score": round(avg_score),
            "areas_to_improve": [
                {"area": gap, "priority": "High", "description": f"Develop stronger {gap} skills"}
                for gap in cv_analysis.get('gaps', [])[:3]
            ]
        }

    # ─────────────────────────────────────────────────────────────────────────
    # COURSE RECOMMENDATION — Guaranteed 3 categories, 2 courses each
    # Category 1: CV Gap      — based on what's missing from their CV
    # Category 2: Field Skills — core free video courses for their exact field
    # Category 3: Interview    — communication, STAR, confidence (always shown)
    # ─────────────────────────────────────────────────────────────────────────
    def recommend_courses(self, feedback: dict, field: str, cv_analysis: dict = None) -> list:
        cv_analysis  = cv_analysis or {}
        cv_gaps      = cv_analysis.get('gaps', [])
        cv_skills    = cv_analysis.get('skills', [])
        level        = cv_analysis.get('experience_level', 'Mid')
        int_gaps     = feedback.get('critical_gaps', [])
        areas        = [a.get('area','') for a in feedback.get('areas_to_improve',[])]
        comm_score   = feedback.get('communication_score', 70)

        # ── CATEGORY 3: Interview Skills — always 2 fixed courses ────────────
        INTERVIEW_COURSES = [
            {
                "category": "Interview Skills",
                "title": "How to Answer Behavioral Interview Questions (STAR Method)",
                "platform": "YouTube — Jeff H Sipe",
                "url": "https://www.youtube.com/watch?v=6MuO0HGnSrU",
                "duration": "45 min",
                "level": "Beginner",
                "rating": 4.9,
                "price": "Free",
                "description": "Master the STAR method — Situation, Task, Action, Result. Learn to structure compelling answers that impress interviewers for any role.",
                "addresses_gap": "Interview answer structure & STAR method"
            },
            {
                "category": "Interview Skills",
                "title": "Public Speaking & Presentation Confidence Full Course",
                "platform": "YouTube — freeCodeCamp",
                "url": "https://www.youtube.com/watch?v=AykAhiMKYss",
                "duration": "2 hours",
                "level": "Beginner",
                "rating": 4.8,
                "price": "Free",
                "description": "Build confidence speaking on camera — delivery, eye contact, body language, handling nerves, and engaging your audience.",
                "addresses_gap": "Communication confidence & body language"
            }
        ]

        # ── CATEGORY 2: Field Skills — mapped by field keyword ────────────────
        # Each entry: list of keywords that match → 2 courses for that field
        FIELD_COURSE_MAP = [
            {
                "keywords": ["wordpress","php","cms","web design","website","blog","woocommerce","elementor","theme"],
                "courses": [
                    {"title":"WordPress Full Course for Beginners","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=O79pJ7qXwoE","duration":"6 hours","level":"Beginner","rating":4.8,"description":"Complete WordPress — themes, plugins, WooCommerce, SEO, and building professional websites from scratch.","addresses_gap":f"{field} core platform skills"},
                    {"title":"PHP Full Course for Beginners","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=OK_JCtrrv-c","duration":"4.5 hours","level":"Beginner","rating":4.8,"description":"PHP fundamentals — syntax, forms, databases, sessions, and WordPress theme/plugin development.","addresses_gap":f"{field} backend development"}
                ]
            },
            {
                "keywords": ["python","django","flask","fastapi","data","scripting","automation","ml","ai","machine learning"],
                "courses": [
                    {"title":"Python Full Course for Beginners","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=rfscVS0vtbw","duration":"4.5 hours","level":"Beginner","rating":4.9,"description":"Complete Python from scratch — OOP, file I/O, APIs, and real projects. Essential for any Python role.","addresses_gap":f"{field} Python proficiency"},
                    {"title":"Django Python Web Framework Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=F5mRW0jo-U4","duration":"3.5 hours","level":"Intermediate","rating":4.8,"description":"Build full-stack apps with Django — models, views, templates, authentication, and REST APIs.","addresses_gap":f"{field} web development"}
                ]
            },
            {
                "keywords": ["javascript","react","vue","angular","node","frontend","typescript","next","nuxt","web developer","web development"],
                "courses": [
                    {"title":"JavaScript Full Course for Beginners","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=PkZNo7MFNFg","duration":"3.5 hours","level":"Beginner","rating":4.9,"description":"Full JavaScript — DOM, events, async/await, ES6+ features, and real projects.","addresses_gap":f"{field} JavaScript skills"},
                    {"title":"React JS Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=bMknfKXIFA8","duration":"8 hours","level":"Intermediate","rating":4.9,"description":"Build production React apps — hooks, state management, routing, and real-world projects.","addresses_gap":f"{field} frontend framework"}
                ]
            },
            {
                "keywords": ["data science","data analyst","data analysis","analytics","pandas","tableau","power bi","excel","reporting","business intelligence"],
                "courses": [
                    {"title":"Data Analysis with Python Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=r-uOLxNrNk8","duration":"4 hours","level":"Beginner","rating":4.9,"description":"Analyse real data with Python and Pandas — cleaning, grouping, visualising, and drawing business insights.","addresses_gap":f"{field} data analysis"},
                    {"title":"SQL Tutorial — Full Database Course for Beginners","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=HXV3zeQKqGY","duration":"4 hours","level":"Beginner","rating":4.9,"description":"Complete SQL — queries, joins, subqueries, aggregate functions, and database design for analytics.","addresses_gap":f"{field} SQL & database skills"}
                ]
            },
            {
                "keywords": ["machine learning","deep learning","tensorflow","pytorch","neural","nlp","ai engineer","artificial intelligence","computer vision"],
                "courses": [
                    {"title":"Machine Learning Full Course with Python","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=NWONeJKn6kc","duration":"10 hours","level":"Intermediate","rating":4.9,"description":"End-to-end ML — regression, classification, clustering, and neural networks with Python and scikit-learn.","addresses_gap":f"{field} ML algorithms"},
                    {"title":"Deep Learning Full Course — TensorFlow & Keras","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=VyWAvY2CF9c","duration":"6 hours","level":"Intermediate","rating":4.8,"description":"Neural networks, CNNs, RNNs, and TensorFlow for real-world deep learning applications.","addresses_gap":f"{field} deep learning"}
                ]
            },
            {
                "keywords": ["devops","docker","kubernetes","cicd","jenkins","aws","cloud","azure","gcp","linux","infrastructure","sre","platform"],
                "courses": [
                    {"title":"Docker Tutorial for Beginners — Full Course","platform":"YouTube — TechWorld with Nana","url":"https://www.youtube.com/watch?v=3c-iBn73dDE","duration":"3 hours","level":"Beginner","rating":4.9,"description":"Docker from zero — images, containers, volumes, networking, Docker Compose, and CI/CD pipelines.","addresses_gap":f"{field} containerisation"},
                    {"title":"AWS Cloud Practitioner Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=SOTamWNgDKc","duration":"13 hours","level":"Beginner","rating":4.9,"description":"Full AWS — core services, IAM, EC2, S3, Lambda, RDS, security, and cloud architecture.","addresses_gap":f"{field} cloud infrastructure"}
                ]
            },
            {
                "keywords": ["cybersecurity","security","ethical hacking","penetration","soc","siem","network security","forensics","vulnerability"],
                "courses": [
                    {"title":"Ethical Hacking Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=3Kq1MIfTWCE","duration":"15 hours","level":"Beginner","rating":4.8,"description":"Full ethical hacking — reconnaissance, scanning, exploitation, post-exploitation, and security tools.","addresses_gap":f"{field} penetration testing"},
                    {"title":"Network Security Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=qiQR5rTSshw","duration":"6 hours","level":"Beginner","rating":4.7,"description":"Network fundamentals and security — TCP/IP, firewalls, VPNs, IDS/IPS, and threat detection.","addresses_gap":f"{field} network security"}
                ]
            },
            {
                "keywords": ["ui","ux","figma","design","product design","user experience","user interface","interaction","wireframe","prototype"],
                "courses": [
                    {"title":"UI/UX Design Full Course — Figma","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=c9Wg6Cb_YlU","duration":"9 hours","level":"Beginner","rating":4.8,"description":"Full UI/UX in Figma — wireframes, user research, prototypes, design systems, and usability testing.","addresses_gap":f"{field} design process"},
                    {"title":"Graphic Design Full Course for Beginners","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=9QTCvayLhCA","duration":"6 hours","level":"Beginner","rating":4.7,"description":"Visual design principles — colour theory, typography, layout, branding, and building a design portfolio.","addresses_gap":f"{field} visual design"}
                ]
            },
            {
                "keywords": ["marketing","digital marketing","seo","social media","content","email marketing","ppc","google ads","ecommerce"],
                "courses": [
                    {"title":"Digital Marketing Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=nU-IIXBWlS4","duration":"6 hours","level":"Beginner","rating":4.8,"description":"Complete digital marketing — SEO, social media, email campaigns, Google Analytics, and paid advertising.","addresses_gap":f"{field} digital marketing"},
                    {"title":"SEO Full Course for Beginners — Ahrefs","platform":"YouTube — Ahrefs","url":"https://www.youtube.com/watch?v=DvwS7cV9GmQ","duration":"2 hours","level":"Beginner","rating":4.8,"description":"SEO from scratch — keyword research, on-page optimisation, link building, and ranking strategies.","addresses_gap":f"{field} SEO skills"}
                ]
            },
            {
                "keywords": ["project management","product management","scrum","agile","jira","pm","program manager","product manager","roadmap"],
                "courses": [
                    {"title":"Project Management Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=GC7pN8Mjot8","duration":"5 hours","level":"Beginner","rating":4.7,"description":"Full PM — waterfall, Agile, Scrum, risk management, stakeholder communication, and project delivery.","addresses_gap":f"{field} project management"},
                    {"title":"Agile & Scrum Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=gy1c4_YixCo","duration":"3 hours","level":"Beginner","rating":4.7,"description":"Agile methodology — sprints, backlogs, retrospectives, Kanban boards, and Jira for project tracking.","addresses_gap":f"{field} Agile methodology"}
                ]
            },
            {
                "keywords": ["finance","accounting","financial","banking","investment","economics","cpa","cfa","budget","audit","tax"],
                "courses": [
                    {"title":"Finance & Accounting Full Course","platform":"Khan Academy","url":"https://www.khanacademy.org/economics-finance-domain/core-finance","duration":"Self-paced","level":"Beginner","rating":4.8,"description":"Complete finance — accounting basics, financial statements, investing, cash flow, and economic principles.","addresses_gap":f"{field} financial knowledge"},
                    {"title":"Excel for Finance & Financial Modelling","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=Vl0H-qTclOg","duration":"3 hours","level":"Beginner","rating":4.8,"description":"Excel for financial analysis — formulas, pivot tables, financial modelling, and reporting dashboards.","addresses_gap":f"{field} financial modelling"}
                ]
            },
            {
                "keywords": ["hr","human resources","recruitment","talent","people","hrbp","people operations","payroll","onboarding"],
                "courses": [
                    {"title":"Human Resources Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=4CcKPCFoJIE","duration":"2.5 hours","level":"Beginner","rating":4.6,"description":"Core HR — recruitment, onboarding, performance management, compensation, and employee relations.","addresses_gap":f"{field} HR fundamentals"},
                    {"title":"Leadership & Team Management Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=iqrFMnbcv-Q","duration":"4 hours","level":"Beginner","rating":4.7,"description":"Leadership skills — delegation, motivation, conflict resolution, and managing diverse teams effectively.","addresses_gap":f"{field} people management"}
                ]
            },
            {
                "keywords": ["sales","business development","crm","salesforce","negotiation","account","b2b","b2c","cold calling","lead generation"],
                "courses": [
                    {"title":"Sales Skills Full Course — How to Sell","platform":"YouTube — Patrick Dang","url":"https://www.youtube.com/watch?v=0zNapGVGXAE","duration":"3 hours","level":"Beginner","rating":4.7,"description":"Complete sales training — prospecting, cold outreach, handling objections, closing deals, and CRM usage.","addresses_gap":f"{field} sales techniques"},
                    {"title":"Negotiation & Persuasion Skills Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=llGSe_ey1j0","duration":"2 hours","level":"Beginner","rating":4.7,"description":"Master negotiation — BATNA, anchoring, win-win strategies, and closing high-value deals.","addresses_gap":f"{field} negotiation skills"}
                ]
            },
            {
                "keywords": ["software","backend","java","c++","c#","golang","rust","api","microservices","architecture","system design","software engineer","software development"],
                "courses": [
                    {"title":"CS50: Introduction to Computer Science","platform":"Harvard (cs50.harvard.edu)","url":"https://cs50.harvard.edu/x/","duration":"12 weeks","level":"Beginner","rating":4.9,"description":"Harvard's legendary CS course — algorithms, data structures, C, Python, SQL, web development, and problem solving.","addresses_gap":f"{field} CS fundamentals"},
                    {"title":"Data Structures & Algorithms Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=pkYVOmU3MgA","duration":"8 hours","level":"Intermediate","rating":4.9,"description":"Master DSA — arrays, trees, graphs, sorting, searching — essential for coding interviews and system design.","addresses_gap":f"{field} algorithmic thinking"}
                ]
            },
        ]

        # ── CATEGORY 1: CV Gap courses — based on actual CV gap keywords ──────
        CV_GAP_POOL = [
            # Communication / Leadership
            {"title":"Communication Skills Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=AykAhiMKYss","duration":"2 hours","level":"Beginner","rating":4.8,"tags":["communication","leadership","soft skills","team","management","speaking","writing","professional"],"description":"Build professional communication — writing, speaking, listening, and presenting ideas clearly in any workplace."},
            # Git / Version Control
            {"title":"Git and GitHub Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=RGOj5yH7evk","duration":"1 hour","level":"Beginner","rating":4.9,"tags":["git","version control","github","collaboration","open source","code","software","devops"],"description":"Complete Git/GitHub — commits, branches, merging, pull requests, and collaboration workflows."},
            # SQL / Database
            {"title":"SQL Tutorial — Full Database Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=HXV3zeQKqGY","duration":"4 hours","level":"Beginner","rating":4.9,"tags":["sql","database","data","queries","mysql","postgresql","backend","analytics"],"description":"Complete SQL — queries, joins, subqueries, indexes, and database design for any developer or analyst."},
            # Python
            {"title":"Python Full Course for Beginners","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=rfscVS0vtbw","duration":"4.5 hours","level":"Beginner","rating":4.9,"tags":["python","programming","scripting","automation","data","backend","coding"],"description":"Complete Python from scratch — variables, loops, OOP, file I/O, and real-world projects."},
            # Cloud
            {"title":"AWS Cloud Practitioner Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=SOTamWNgDKc","duration":"13 hours","level":"Beginner","rating":4.9,"tags":["cloud","aws","azure","gcp","infrastructure","devops","deployment","serverless"],"description":"Full AWS cloud fundamentals — services, security, pricing, and architecture for any cloud role."},
            # Docker
            {"title":"Docker Tutorial for Beginners","platform":"YouTube — TechWorld with Nana","url":"https://www.youtube.com/watch?v=3c-iBn73dDE","duration":"3 hours","level":"Beginner","rating":4.9,"tags":["docker","containers","devops","kubernetes","deployment","cicd","microservices"],"description":"Docker from zero — images, containers, networking, Docker Compose, and CI/CD integration."},
            # Agile
            {"title":"Agile & Scrum Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=gy1c4_YixCo","duration":"3 hours","level":"Beginner","rating":4.7,"tags":["agile","scrum","jira","sprint","project management","kanban","team","planning"],"description":"Agile methodology — sprints, backlogs, retrospectives, and Kanban for any team or project."},
            # Excel / Data
            {"title":"Microsoft Excel Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=Vl0H-qTclOg","duration":"3 hours","level":"Beginner","rating":4.8,"tags":["excel","spreadsheet","data","reporting","finance","analytics","business","formulas"],"description":"Complete Excel — formulas, pivot tables, VLOOKUP, charts, and data analysis dashboards."},
            # DSA
            {"title":"Data Structures & Algorithms Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=pkYVOmU3MgA","duration":"8 hours","level":"Intermediate","rating":4.9,"tags":["algorithms","data structures","problem solving","coding","interview","computer science","logic"],"description":"Master DSA — arrays, trees, graphs, sorting, and searching. Essential for technical interviews."},
            # JavaScript
            {"title":"JavaScript Full Course for Beginners","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=PkZNo7MFNFg","duration":"3.5 hours","level":"Beginner","rating":4.9,"tags":["javascript","frontend","web","dom","es6","programming","html","css"],"description":"Full JavaScript — DOM manipulation, events, async/await, ES6+, and real-world web projects."},
            # Linux
            {"title":"Linux Command Line Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=ZtqBQ68cfJc","duration":"5 hours","level":"Beginner","rating":4.8,"tags":["linux","command line","bash","server","shell","terminal","devops","system","administration"],"description":"Master the Linux terminal — navigation, file management, permissions, shell scripting, and server admin."},
            # Figma / Design
            {"title":"Figma UI Design Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=c9Wg6Cb_YlU","duration":"9 hours","level":"Beginner","rating":4.8,"tags":["figma","design","ui","ux","prototype","wireframe","visual","product design","creative"],"description":"Figma from scratch — components, design systems, prototyping, and handing off designs to developers."},
            # SEO
            {"title":"SEO Full Course for Beginners","platform":"YouTube — Ahrefs","url":"https://www.youtube.com/watch?v=DvwS7cV9GmQ","duration":"2 hours","level":"Beginner","rating":4.8,"tags":["seo","marketing","search","keywords","content","digital marketing","ranking","website","analytics"],"description":"SEO from scratch — keyword research, on-page SEO, link building, and Google ranking strategies."},
            # Leadership / Management
            {"title":"Leadership & Management Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=iqrFMnbcv-Q","duration":"4 hours","level":"Beginner","rating":4.7,"tags":["leadership","management","team","decision","conflict","people","strategy","motivation","soft skills"],"description":"Leadership skills — delegation, motivation, conflict resolution, decision-making, and team management."},
            # React
            {"title":"React JS Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=bMknfKXIFA8","duration":"8 hours","level":"Intermediate","rating":4.9,"tags":["react","frontend","javascript","components","hooks","state","web","ui","typescript"],"description":"Build production React apps — hooks, context, routing, state management, and real projects."},
            # ML
            {"title":"Machine Learning Full Course","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=NWONeJKn6kc","duration":"10 hours","level":"Intermediate","rating":4.9,"tags":["machine learning","ai","python","scikit","neural","algorithms","data science","modeling","prediction"],"description":"End-to-end ML — regression, classification, clustering, neural networks, and model evaluation."},
        ]

        # ── Step 1: Pick field courses ────────────────────────────────────────
        field_lower = field.lower()
        field_courses = None
        for entry in FIELD_COURSE_MAP:
            if any(kw in field_lower for kw in entry["keywords"]):
                field_courses = entry["courses"]
                break
        # Default fallback for unknown fields — use CS50 + Communication
        if not field_courses:
            field_courses = [
                {"title":"CS50: Introduction to Computer Science","platform":"Harvard (cs50.harvard.edu)","url":"https://cs50.harvard.edu/x/","duration":"12 weeks","level":"Beginner","rating":4.9,"description":"Harvard's legendary CS course — algorithms, data structures, Python, SQL, and web development.","addresses_gap":f"{field} technical foundations"},
                {"title":"Professional Skills & Workplace Communication","platform":"YouTube — freeCodeCamp","url":"https://www.youtube.com/watch?v=AykAhiMKYss","duration":"2 hours","level":"Beginner","rating":4.8,"description":"Core professional skills — communication, collaboration, problem solving, and workplace effectiveness.","addresses_gap":f"{field} professional skills"}
            ]
        # Tag field courses with category
        for c in field_courses:
            c["category"] = "Field Skills"
            c.setdefault("addresses_gap", f"{field} core skills")

        # ── Step 2: Pick CV gap courses ───────────────────────────────────────
        # Match CV gaps against course tags
        gap_text = ' '.join(cv_gaps + int_gaps + areas + cv_skills).lower()

        def gap_score(course):
            return sum(1 for tag in course.get('tags', []) if tag in gap_text)

        scored_gap = sorted(CV_GAP_POOL, key=gap_score, reverse=True)

        # Avoid duplicating field courses
        field_urls = {c['url'] for c in field_courses}
        cv_courses = []
        seen_urls = set(field_urls)
        for c in scored_gap:
            if c['url'] not in seen_urls:
                cv_c = dict(c)
                cv_c["category"] = "CV Gap"
                # Label what gap it addresses
                matched = [tag for tag in c.get('tags', []) if tag in gap_text]
                cv_c["addresses_gap"] = matched[0].title() + " skill gap" if matched else (cv_gaps[0] if cv_gaps else "CV skill gap")
                cv_courses.append(cv_c)
                seen_urls.add(c['url'])
            if len(cv_courses) == 2:
                break

        # Fallback if not enough CV gap courses
        while len(cv_courses) < 2:
            cv_courses.append({
                "category": "CV Gap",
                "title": "Data Structures & Algorithms Full Course",
                "platform": "YouTube — freeCodeCamp",
                "url": "https://www.youtube.com/watch?v=pkYVOmU3MgA",
                "duration": "8 hours", "level": "Intermediate", "rating": 4.9, "price": "Free",
                "description": "Master DSA — arrays, trees, graphs, sorting, searching. Essential for any technical interview.",
                "addresses_gap": "Problem solving & algorithmic thinking"
            })

        # ── Step 3: Combine all 3 categories in order ─────────────────────────
        all_courses = cv_courses[:2] + field_courses[:2] + INTERVIEW_COURSES[:2]
        for c in all_courses:
            c['price'] = 'Free'

        return all_courses