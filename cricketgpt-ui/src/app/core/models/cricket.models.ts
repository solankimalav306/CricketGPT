// ─────────────────────────────────────────────────────────
// Pipeline Step (Thinking)
// ─────────────────────────────────────────────────────────
export interface PipelineStep {
  id: string;
  label: string;
  icon: string;
  status: 'pending' | 'running' | 'done' | 'error';
  summary: string;
  detail: Record<string, unknown>;
}

export interface ThinkingData {
  steps: PipelineStep[];
}

// ─────────────────────────────────────────────────────────
// Win Probability
// ─────────────────────────────────────────────────────────
export interface TeamProb {
  name: string;
  value: number;
}

export interface WinProbability {
  team_a?: TeamProb;
  team_b?: TeamProb;
  draw?: TeamProb;
}

// ─────────────────────────────────────────────────────────
// Why Bullet
// ─────────────────────────────────────────────────────────
export interface WhyBullet {
  label: string;
  text: string;
}

// ─────────────────────────────────────────────────────────
// Answer Sections
// ─────────────────────────────────────────────────────────
export interface AnswerSections {
  raw: string;
  prediction: string;
  win_probability: WinProbability;
  win_probability_raw: string;
  why: WhyBullet[];
  why_raw: string;
  verdict: string;
}

// ─────────────────────────────────────────────────────────
// API Response
// ─────────────────────────────────────────────────────────
export interface CricketResponse {
  query: string;
  thinking: ThinkingData;
  answer: AnswerSections;
  html?: string;
}

export interface QueryRequest {
  query: string;
}
