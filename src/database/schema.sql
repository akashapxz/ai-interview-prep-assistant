-- ============================================================
-- AI Interview Preparation Assistant - PostgreSQL Schema
-- Run this entire file in your Supabase SQL Editor
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- profiles
-- ============================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL DEFAULT '',
    email TEXT UNIQUE NOT NULL,
    avatar_url TEXT,
    college TEXT,
    branch TEXT,
    graduation_year INTEGER,
    phone TEXT,
    linkedin_url TEXT,
    github_url TEXT,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin')),
    xp_points INTEGER NOT NULL DEFAULT 0,
    streak_days INTEGER NOT NULL DEFAULT 0,
    last_active DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- resumes
-- ============================================================
CREATE TABLE IF NOT EXISTS public.resumes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_url TEXT NOT NULL,
    file_size INTEGER,
    parsed_text TEXT,
    skills JSONB DEFAULT '[]',
    education JSONB DEFAULT '[]',
    experience JSONB DEFAULT '[]',
    projects JSONB DEFAULT '[]',
    certifications JSONB DEFAULT '[]',
    summary TEXT,
    ats_score INTEGER DEFAULT 0,
    readiness_score INTEGER DEFAULT 0,
    strengths JSONB DEFAULT '[]',
    weaknesses JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- interviews
-- ============================================================
CREATE TABLE IF NOT EXISTS public.interviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    interview_type TEXT NOT NULL CHECK (interview_type IN ('technical','hr','coding','mock','voice','company_specific')),
    domain TEXT,
    company TEXT,
    difficulty TEXT CHECK (difficulty IN ('easy','medium','hard')),
    persona TEXT,
    status TEXT NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress','completed','abandoned')),
    overall_score NUMERIC(5,2) DEFAULT 0,
    technical_score NUMERIC(5,2) DEFAULT 0,
    hr_score NUMERIC(5,2) DEFAULT 0,
    communication_score NUMERIC(5,2) DEFAULT 0,
    confidence_score NUMERIC(5,2) DEFAULT 0,
    coding_score NUMERIC(5,2) DEFAULT 0,
    duration_minutes INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,
    answered_questions INTEGER DEFAULT 0,
    feedback TEXT,
    report_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- ============================================================
-- interview_questions
-- ============================================================
CREATE TABLE IF NOT EXISTS public.interview_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interview_id UUID NOT NULL REFERENCES public.interviews(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type TEXT NOT NULL CHECK (question_type IN ('conceptual','scenario','problem_solving','behavioral','coding','system_design')),
    domain TEXT,
    difficulty TEXT CHECK (difficulty IN ('easy','medium','hard')),
    expected_answer TEXT,
    hints JSONB DEFAULT '[]',
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- responses
-- ============================================================
CREATE TABLE IF NOT EXISTS public.responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL REFERENCES public.interview_questions(id) ON DELETE CASCADE,
    interview_id UUID NOT NULL REFERENCES public.interviews(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    answer_text TEXT,
    score NUMERIC(5,2) DEFAULT 0,
    accuracy_score NUMERIC(5,2) DEFAULT 0,
    depth_score NUMERIC(5,2) DEFAULT 0,
    clarity_score NUMERIC(5,2) DEFAULT 0,
    completeness_score NUMERIC(5,2) DEFAULT 0,
    ai_feedback TEXT,
    model_answer TEXT,
    time_taken_seconds INTEGER DEFAULT 0,
    is_bookmarked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- coding_sessions
-- ============================================================
CREATE TABLE IF NOT EXISTS public.coding_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    interview_id UUID REFERENCES public.interviews(id) ON DELETE SET NULL,
    problem_title TEXT NOT NULL,
    problem_description TEXT NOT NULL,
    topic TEXT NOT NULL,
    difficulty TEXT CHECK (difficulty IN ('easy','medium','hard')),
    language TEXT NOT NULL DEFAULT 'python',
    user_code TEXT,
    ai_solution TEXT,
    test_cases JSONB DEFAULT '[]',
    correctness_score NUMERIC(5,2) DEFAULT 0,
    time_complexity TEXT,
    space_complexity TEXT,
    best_practices_score NUMERIC(5,2) DEFAULT 0,
    overall_score NUMERIC(5,2) DEFAULT 0,
    ai_feedback TEXT,
    hints_used INTEGER DEFAULT 0,
    time_taken_seconds INTEGER DEFAULT 0,
    status TEXT DEFAULT 'attempted' CHECK (status IN ('attempted','solved','failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- performance_metrics
-- ============================================================
CREATE TABLE IF NOT EXISTS public.performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL DEFAULT CURRENT_DATE,
    technical_score NUMERIC(5,2) DEFAULT 0,
    hr_score NUMERIC(5,2) DEFAULT 0,
    coding_score NUMERIC(5,2) DEFAULT 0,
    communication_score NUMERIC(5,2) DEFAULT 0,
    confidence_score NUMERIC(5,2) DEFAULT 0,
    overall_score NUMERIC(5,2) DEFAULT 0,
    interviews_completed INTEGER DEFAULT 0,
    problems_solved INTEGER DEFAULT 0,
    study_minutes INTEGER DEFAULT 0,
    weak_areas JSONB DEFAULT '[]',
    strong_areas JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, metric_date)
);

-- ============================================================
-- achievements
-- ============================================================
CREATE TABLE IF NOT EXISTS public.achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    icon TEXT NOT NULL DEFAULT '🏆',
    xp_reward INTEGER NOT NULL DEFAULT 50,
    badge_color TEXT DEFAULT '#6366f1',
    criteria JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.user_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES public.achievements(id) ON DELETE CASCADE,
    earned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, achievement_id)
);

-- ============================================================
-- leaderboard
-- ============================================================
CREATE TABLE IF NOT EXISTS public.leaderboard (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    week_start DATE NOT NULL,
    xp_gained INTEGER DEFAULT 0,
    interviews_completed INTEGER DEFAULT 0,
    problems_solved INTEGER DEFAULT 0,
    avg_score NUMERIC(5,2) DEFAULT 0,
    rank INTEGER,
    UNIQUE(user_id, week_start)
);

-- ============================================================
-- uploaded_documents (RAG)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.uploaded_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_url TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER,
    doc_type TEXT DEFAULT 'general',
    chunk_count INTEGER DEFAULT 0,
    is_indexed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES public.uploaded_documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- chat_history
-- ============================================================
CREATE TABLE IF NOT EXISTS public.chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    chat_type TEXT DEFAULT 'rag' CHECK (chat_type IN ('rag','career_coach','interview')),
    role TEXT NOT NULL CHECK (role IN ('user','assistant')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- recommendations
-- ============================================================
CREATE TABLE IF NOT EXISTS public.recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    roadmap JSONB NOT NULL DEFAULT '[]',
    weak_areas JSONB DEFAULT '[]',
    focus_topics JSONB DEFAULT '[]',
    weekly_goals JSONB DEFAULT '[]',
    estimated_readiness_date DATE,
    readiness_score INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- voice_sessions
-- ============================================================
CREATE TABLE IF NOT EXISTS public.voice_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interview_id UUID REFERENCES public.interviews(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    transcript TEXT,
    audio_url TEXT,
    speaking_speed NUMERIC(5,2),
    filler_word_count INTEGER DEFAULT 0,
    filler_words JSONB DEFAULT '[]',
    confidence_score NUMERIC(5,2) DEFAULT 0,
    communication_score NUMERIC(5,2) DEFAULT 0,
    clarity_score NUMERIC(5,2) DEFAULT 0,
    ai_analysis TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- company_preparation
-- ============================================================
CREATE TABLE IF NOT EXISTS public.company_preparation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    company_name TEXT NOT NULL,
    readiness_score INTEGER DEFAULT 0,
    sessions_completed INTEGER DEFAULT 0,
    last_practiced_at TIMESTAMPTZ,
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, company_name)
);

-- ============================================================
-- audit_logs
-- ============================================================
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource TEXT,
    resource_id TEXT,
    metadata JSONB DEFAULT '{}',
    ip_address TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- daily_challenges
-- ============================================================
CREATE TABLE IF NOT EXISTS public.daily_challenges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    challenge_date DATE NOT NULL DEFAULT CURRENT_DATE,
    challenge_type TEXT NOT NULL CHECK (challenge_type IN ('technical','hr','coding')),
    question TEXT NOT NULL,
    domain TEXT,
    difficulty TEXT DEFAULT 'medium',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(challenge_date)
);

CREATE TABLE IF NOT EXISTS public.user_daily_challenges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    challenge_id UUID NOT NULL REFERENCES public.daily_challenges(id) ON DELETE CASCADE,
    answer_text TEXT,
    score NUMERIC(5,2) DEFAULT 0,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, challenge_id)
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_interviews_user_id ON public.interviews(user_id);
CREATE INDEX IF NOT EXISTS idx_interviews_created ON public.interviews(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_responses_interview ON public.responses(interview_id);
CREATE INDEX IF NOT EXISTS idx_responses_bookmarked ON public.responses(is_bookmarked) WHERE is_bookmarked = TRUE;
CREATE INDEX IF NOT EXISTS idx_coding_sessions_user ON public.coding_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_performance_user_date ON public.performance_metrics(user_id, metric_date DESC);
CREATE INDEX IF NOT EXISTS idx_chat_history_session ON public.chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_doc ON public.knowledge_base(document_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON public.audit_logs(user_id);

-- ============================================================
-- TRIGGERS
-- ============================================================
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_resumes_updated_at
    BEFORE UPDATE ON public.resumes
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url)
    VALUES (
        NEW.id, NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
        COALESCE(NEW.raw_user_meta_data->>'avatar_url', '')
    ) ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

CREATE OR REPLACE FUNCTION public.award_xp(p_user_id UUID, p_xp INTEGER)
RETURNS VOID AS $$
BEGIN
    UPDATE public.profiles SET xp_points = xp_points + p_xp, updated_at = NOW()
    WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================
-- SEED ACHIEVEMENTS
-- ============================================================
INSERT INTO public.achievements (name, description, icon, xp_reward, criteria) VALUES
('First Interview','Completed your first mock interview','🎯',100,'{"interviews_completed":1}'),
('Interview Pro','Completed 5 mock interviews','⭐',250,'{"interviews_completed":5}'),
('Interview Master','Completed 10 mock interviews','🏆',500,'{"interviews_completed":10}'),
('Code Warrior','Solved 10 coding problems','💻',200,'{"problems_solved":10}'),
('Code Legend','Solved 50 coding problems','🔥',750,'{"problems_solved":50}'),
('7-Day Streak','Maintained a 7-day practice streak','⚡',300,'{"streak_days":7}'),
('30-Day Streak','Maintained a 30-day practice streak','🌟',1000,'{"streak_days":30}'),
('Resume Ready','Uploaded and analyzed your resume','📄',50,'{"resume_uploaded":true}'),
('Perfect Score','Scored 95+ in any interview','💯',500,'{"max_score":95}'),
('RAG Explorer','Used the knowledge assistant 10 times','🧠',150,'{"rag_queries":10}'),
('Company Crusher','Prepared for 5 different companies','🏢',400,'{"companies_practiced":5}'),
('Voice Master','Completed 3 voice interviews','🎙️',200,'{"voice_interviews":3}')
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coding_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.leaderboard ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.uploaded_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_base ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.voice_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.company_preparation ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_daily_challenges ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

CREATE POLICY "Users can view own profile" ON public.profiles FOR SELECT USING (auth.uid()=id);
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING (auth.uid()=id);
CREATE POLICY "Admins view all profiles" ON public.profiles FOR ALL USING (public.is_admin());
CREATE POLICY "Own resumes" ON public.resumes FOR ALL USING (auth.uid()=user_id);
CREATE POLICY "Own interviews" ON public.interviews FOR ALL USING (auth.uid()=user_id);
CREATE POLICY "Own questions" ON public.interview_questions FOR ALL USING (auth.uid()=user_id);
CREATE POLICY "Own responses" ON public.responses FOR ALL USING (auth.uid()=user_id);
CREATE POLICY "Own coding sessions" ON public.coding_sessions FOR ALL USING (auth.uid()=user_id);
CREATE POLICY "Own performance" ON public.performance_metrics FOR ALL USING (auth.uid()=user_id);
CREATE POLICY "Own achievements" ON public.user_achievements FOR ALL USING (auth.uid()=user_id);
CREATE POLICY "Own leaderboard" ON public.leaderboard FOR SELECT USING (auth.uid()=user_id);
CREATE POLICY "Own documents" ON public.uploaded_documents FOR ALL USING (auth.uid()=user_id);
CREATE POLICY "Own knowledge" ON public.knowledge_base FOR ALL USING (auth.uid()=user_id);
CREATE POLICY "Own chat" ON public.chat_history FOR ALL USING (auth.uid()=user_id);
CREATE POLICY "Own recommendations" ON public.recommendations FOR ALL USING (auth.uid()=user_id);
CREATE POLICY "Own voice sessions" ON public.voice_sessions FOR ALL USING (auth.uid()=user_id);
CREATE POLICY "Own company prep" ON public.company_preparation FOR ALL USING (auth.uid()=user_id);
CREATE POLICY "Own daily challenges" ON public.user_daily_challenges FOR ALL USING (auth.uid()=user_id);
CREATE POLICY "Public achievements" ON public.achievements FOR SELECT USING (true);
CREATE POLICY "Public leaderboard read" ON public.leaderboard FOR SELECT USING (true);
CREATE POLICY "Public daily challenges" ON public.daily_challenges FOR SELECT USING (true);
