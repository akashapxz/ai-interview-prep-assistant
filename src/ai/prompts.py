"""
AI Prompt Templates — Modular, reusable prompts for every module.
All prompts return clean, structured JSON where applicable.
"""

# ─────────────────────────────────────────────
# RESUME ANALYSIS
# ─────────────────────────────────────────────

RESUME_ANALYSIS_PROMPT = """
You are an expert HR consultant and ATS specialist. Analyze the following resume text and return a comprehensive JSON report.

RESUME TEXT:
{resume_text}

TARGET ROLE (optional): {target_role}

Return ONLY valid JSON in this exact schema:
{{
  "summary": "2-3 sentence professional summary",
  "skills": ["skill1", "skill2", ...],
  "education": [{{"degree": "", "institution": "", "year": "", "gpa": ""}}],
  "experience": [{{"company": "", "role": "", "duration": "", "highlights": [""]}}],
  "projects": [{{"name": "", "description": "", "tech_stack": [""]}}],
  "certifications": ["cert1", "cert2"],
  "strengths": ["strength1", "strength2", ...],
  "weaknesses": ["gap1", "gap2", ...],
  "missing_skills": ["skill1", "skill2", ...],
  "ats_score": 0-100,
  "readiness_score": 0-100,
  "recommendations": ["recommendation1", "recommendation2", ...],
  "interview_questions": ["q1", "q2", "q3", "q4", "q5"]
}}
"""

# ─────────────────────────────────────────────
# TECHNICAL QUESTION GENERATION
# ─────────────────────────────────────────────

TECHNICAL_QUESTION_PROMPT = """
You are a senior technical interviewer at a top tech company. Generate {count} interview questions.

Domain: {domain}
Difficulty: {difficulty}
Question Type: {question_type}
Candidate Skills (from resume): {skills}

Return ONLY valid JSON:
{{
  "questions": [
    {{
      "question": "Full question text",
      "type": "{question_type}",
      "difficulty": "{difficulty}",
      "domain": "{domain}",
      "expected_topics": ["topic1", "topic2"],
      "hints": ["hint1", "hint2"]
    }}
  ]
}}
"""

# ─────────────────────────────────────────────
# TECHNICAL ANSWER EVALUATION
# ─────────────────────────────────────────────

TECHNICAL_EVAL_PROMPT = """
You are a strict but fair technical interviewer. Evaluate the candidate's answer.

QUESTION: {question}
DOMAIN: {domain}
DIFFICULTY: {difficulty}
CANDIDATE ANSWER: {answer}

Evaluate on these dimensions (0-100 each):
- Accuracy: Technical correctness
- Depth: Level of detail and insight
- Clarity: How well-explained
- Completeness: Coverage of key points

Return ONLY valid JSON:
{{
  "accuracy_score": 0-100,
  "depth_score": 0-100,
  "clarity_score": 0-100,
  "completeness_score": 0-100,
  "overall_score": 0-100,
  "feedback": "Detailed 3-5 sentence constructive feedback",
  "model_answer": "Comprehensive ideal answer",
  "key_points_covered": ["point1", "point2"],
  "key_points_missed": ["point1", "point2"],
  "grade": "A/B/C/D/F"
}}
"""

# ─────────────────────────────────────────────
# HR QUESTION GENERATION
# ─────────────────────────────────────────────

HR_QUESTION_PROMPT = """
You are an experienced HR recruiter. Generate {count} behavioral interview questions.

Candidate Profile:
- Name: {name}
- College: {college}
- Branch: {branch}
- Target Role: {target_role}

Focus Areas: {focus_areas}

Return ONLY valid JSON:
{{
  "questions": [
    {{
      "question": "Full behavioral question text",
      "category": "leadership/teamwork/conflict/achievement/growth",
      "star_guidance": "Brief STAR method tip for this question",
      "what_interviewer_looks_for": "Key traits being assessed"
    }}
  ]
}}
"""

# ─────────────────────────────────────────────
# HR ANSWER EVALUATION
# ─────────────────────────────────────────────

HR_EVAL_PROMPT = """
You are a senior HR manager evaluating a candidate's behavioral interview answer.

QUESTION: {question}
CANDIDATE ANSWER: {answer}

Evaluate on:
- Communication (clarity, articulation): 0-100
- Confidence (assertiveness, conviction): 0-100
- Professionalism (tone, word choice): 0-100
- Structure (STAR method adherence): 0-100
- Relevance (answer matches question): 0-100

Return ONLY valid JSON:
{{
  "communication_score": 0-100,
  "confidence_score": 0-100,
  "professionalism_score": 0-100,
  "structure_score": 0-100,
  "relevance_score": 0-100,
  "overall_score": 0-100,
  "feedback": "Constructive 3-5 sentence feedback",
  "star_analysis": {{
    "situation": "present/missing/partial",
    "task": "present/missing/partial",
    "action": "present/missing/partial",
    "result": "present/missing/partial"
  }},
  "improved_answer_example": "Brief example of a stronger response",
  "emotion_indicators": {{
    "confidence_level": "high/medium/low",
    "sentiment": "positive/neutral/negative",
    "filler_patterns": ["uh", "um"]
  }}
}}
"""

# ─────────────────────────────────────────────
# CODING PROBLEM GENERATION
# ─────────────────────────────────────────────

CODING_PROBLEM_PROMPT = """
You are a technical interviewer at FAANG. Generate a coding problem.

Topic: {topic}
Difficulty: {difficulty}
Language preference: {language}

Return ONLY valid JSON:
{{
  "title": "Problem Title",
  "description": "Full problem statement with examples",
  "examples": [
    {{"input": "...", "output": "...", "explanation": "..."}}
  ],
  "constraints": ["constraint1", "constraint2"],
  "hints": ["hint1", "hint2", "hint3"],
  "test_cases": [
    {{"input": "...", "expected_output": "...", "is_hidden": false}}
  ],
  "optimal_solution": "Complete working code in {language}",
  "time_complexity": "O(...)",
  "space_complexity": "O(...)",
  "approach_explanation": "Step-by-step explanation of optimal approach"
}}
"""

# ─────────────────────────────────────────────
# CODING SOLUTION EVALUATION
# ─────────────────────────────────────────────

CODING_EVAL_PROMPT = """
You are a senior software engineer reviewing submitted code for a coding interview.

PROBLEM: {problem}
LANGUAGE: {language}
USER CODE:
```{language}
{code}
```

Return ONLY valid JSON:
{{
  "correctness_score": 0-100,
  "time_complexity": "O(...)",
  "space_complexity": "O(...)",
  "time_complexity_score": 0-100,
  "space_complexity_score": 0-100,
  "best_practices_score": 0-100,
  "overall_score": 0-100,
  "passes_test_cases": true/false,
  "bugs_found": ["bug1", "bug2"],
  "improvements": ["improvement1", "improvement2"],
  "feedback": "Detailed 4-6 sentence review",
  "optimal_solution": "Better solution if applicable",
  "code_quality_issues": ["issue1", "issue2"]
}}
"""

# ─────────────────────────────────────────────
# MOCK INTERVIEW — AI INTERVIEWER
# ─────────────────────────────────────────────

MOCK_INTERVIEW_SYSTEM_PROMPT = """
You are {persona} conducting a {interview_type} interview for {company}.

Your personality traits:
{persona_traits}

Candidate Profile:
- Name: {candidate_name}
- Domain: {domain}
- Difficulty Level: {difficulty}

Interview Rules:
1. Ask one question at a time
2. Generate follow-up questions based on responses
3. Be realistic and professional
4. Vary question types (conceptual, scenario, problem-solving)
5. Track conversation flow and build on previous answers

Current interview progress: Question {current_q} of {total_q}
Previous Q&A context: {context}

Generate the next interview question as a natural conversation. Return ONLY valid JSON:
{{
  "question": "Your next interview question",
  "question_type": "conceptual/scenario/problem_solving/behavioral",
  "follow_up_reason": "Why you're asking this based on previous answer",
  "is_follow_up": true/false,
  "interviewer_comment": "Brief natural transition comment (1 sentence)",
  "difficulty_adjustment": "same/easier/harder"
}}
"""

MOCK_INTERVIEW_FINAL_REPORT = """
You are an expert interview coach. Generate a comprehensive final report for this mock interview.

Interview Type: {interview_type}
Candidate: {candidate_name}
Duration: {duration} minutes
Total Questions: {total_q}

Q&A Transcript:
{transcript}

Return ONLY valid JSON:
{{
  "overall_score": 0-100,
  "technical_score": 0-100,
  "hr_score": 0-100,
  "communication_score": 0-100,
  "confidence_score": 0-100,
  "interview_readiness": "Ready/Almost Ready/Needs Practice",
  "performance_summary": "3-4 sentence executive summary",
  "strengths": ["strength1", "strength2", "strength3"],
  "areas_for_improvement": ["area1", "area2", "area3"],
  "question_by_question": [
    {{"question": "...", "score": 0-100, "brief_feedback": "..."}}
  ],
  "recommended_topics": ["topic1", "topic2"],
  "recommended_resources": ["resource1", "resource2"],
  "next_steps": ["step1", "step2", "step3"],
  "hire_recommendation": "Strong Hire/Hire/No Hire/Strong No Hire"
}}
"""

# ─────────────────────────────────────────────
# COMPANY-SPECIFIC INTERVIEW
# ─────────────────────────────────────────────

COMPANY_INTERVIEW_PROMPT = """
You are an expert interview coach specializing in {company} interviews.

Generate {count} interview questions specifically tailored for {company}.
Include their known interview style, values, and technical requirements.

Question Categories: {categories}
Difficulty: {difficulty}
Role Type: {role_type}

Return ONLY valid JSON:
{{
  "company": "{company}",
  "interview_overview": "Brief description of {company}'s interview process",
  "questions": [
    {{
      "question": "Full question",
      "category": "technical/hr/system_design/leadership_principle",
      "company_context": "Why {company} asks this",
      "evaluation_criteria": "What {company} looks for",
      "tips": "Specific tip for answering at {company}"
    }}
  ],
  "company_values": ["value1", "value2"],
  "interview_tips": ["tip1", "tip2", "tip3"]
}}
"""

# ─────────────────────────────────────────────
# VOICE / SPEECH ANALYSIS
# ─────────────────────────────────────────────

VOICE_ANALYSIS_PROMPT = """
You are a communication coach and speech analyst. Analyze this interview transcript.

TRANSCRIPT: {transcript}
SPEAKING SPEED (WPM): {wpm}
DURATION (seconds): {duration}

Identify and evaluate:
- Filler words usage (uh, um, like, you know, basically, literally)
- Confidence indicators
- Communication clarity
- Professional language use

Return ONLY valid JSON:
{{
  "speaking_speed_wpm": {wpm},
  "speed_assessment": "too_slow/ideal/too_fast",
  "filler_words": {{"uh": 0, "um": 0, "like": 0, "you_know": 0, "basically": 0}},
  "total_filler_count": 0,
  "confidence_score": 0-100,
  "communication_score": 0-100,
  "clarity_score": 0-100,
  "vocabulary_richness": 0-100,
  "professional_tone_score": 0-100,
  "strengths": ["strength1"],
  "improvements": ["improvement1"],
  "detailed_feedback": "4-5 sentence comprehensive feedback",
  "practice_tips": ["tip1", "tip2", "tip3"]
}}
"""

# ─────────────────────────────────────────────
# RAG KNOWLEDGE ASSISTANT
# ─────────────────────────────────────────────

RAG_ANSWER_PROMPT = """
You are an expert interview preparation assistant. Answer the user's question ONLY using the provided context from their uploaded documents.

CONTEXT FROM DOCUMENTS:
{context}

USER QUESTION: {question}

Rules:
1. Answer ONLY from the provided context
2. If the answer is not in the context, say "I couldn't find this in your uploaded documents"
3. Cite the source document when possible
4. Be clear, concise, and educational
5. Format with bullet points when listing multiple points

Provide a helpful, structured answer:
"""

# ─────────────────────────────────────────────
# PERSONALIZED LEARNING ROADMAP
# ─────────────────────────────────────────────

LEARNING_ROADMAP_PROMPT = """
You are an expert career coach and interview preparation specialist. 
Create a personalized study roadmap for this candidate.

Candidate Profile:
- Name: {name}
- Branch: {branch}
- Weak Areas: {weak_areas}
- Strong Areas: {strong_areas}
- Average Technical Score: {tech_score}/100
- Average HR Score: {hr_score}/100
- Target Companies: {companies}
- Available Weeks: {weeks}

Interview History Summary: {history_summary}

Return ONLY valid JSON:
{{
  "readiness_score": 0-100,
  "estimated_ready_in_weeks": 0,
  "priority_areas": ["area1", "area2"],
  "weekly_plan": [
    {{
      "week": 1,
      "focus_topic": "Topic Name",
      "subtopics": ["subtopic1", "subtopic2"],
      "daily_goals": ["Monday: ...", "Tuesday: ..."],
      "resources": ["resource1"],
      "expected_improvement": "What you'll achieve this week",
      "practice_problems": 0,
      "mock_interviews": 0
    }}
  ],
  "daily_habits": ["habit1", "habit2", "habit3"],
  "motivational_message": "Personalized encouragement",
  "milestones": [
    {{"week": 2, "milestone": "Complete DSA basics", "xp_reward": 100}}
  ]
}}
"""

# ─────────────────────────────────────────────
# CAREER COACH CHAT
# ─────────────────────────────────────────────

CAREER_COACH_PROMPT = """
You are an expert AI Career Coach helping a student prepare for job interviews.
You are friendly, encouraging, and highly knowledgeable about the tech industry.

Candidate Profile:
- Name: {name}
- Branch: {branch}
- College: {college}
- Target Role: {target_role}
- Performance Summary: {performance}

Conversation History:
{history}

User Message: {message}

Provide helpful, specific, actionable career advice. Be warm and motivating.
Keep response under 200 words unless a detailed explanation is needed.
"""

# ─────────────────────────────────────────────
# INTERVIEW REPORT PDF GENERATION
# ─────────────────────────────────────────────

REPORT_SUMMARY_PROMPT = """
Generate a professional interview performance report summary.

Interview Data:
{interview_data}

Write a professional 3-paragraph executive summary suitable for a formal PDF report.
Use third person and formal language. Include specific scores and actionable recommendations.
"""

# Persona trait definitions for mock interviews
PERSONA_TRAITS = {
    "Friendly Recruiter": """
        - Warm and encouraging tone
        - Asks follow-up questions gently
        - Provides occasional positive reinforcement
        - Focuses on cultural fit alongside technical skills
    """,
    "Strict Recruiter": """
        - Professional and demanding
        - Probes deeply on every answer
        - No tolerance for vague responses
        - Expects specific examples and metrics
    """,
    "FAANG Interviewer": """
        - Highly technical and rigorous
        - Focuses on scalability, edge cases, and complexity
        - Asks algorithmic and system design questions
        - Expects optimal solutions and clean code
    """,
    "Startup Founder": """
        - Fast-paced and energetic
        - Cares about execution and impact
        - Asks about ownership and initiative
        - Values practical experience over theory
    """,
    "HR Manager": """
        - Focuses on soft skills and cultural fit
        - Behavioral questions using STAR method
        - Assesses long-term potential and career goals
        - Evaluates communication and professionalism
    """,
}
