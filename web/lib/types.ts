export type PersonStatus =
  | "queued"
  | "scraping"
  | "scraped"
  | "analyzing"
  | "analyzed"
  | "failed";

export interface PersonOut {
  id: number;
  name: string;
  linkedin_url: string;
  instagram_url: string;
  status: PersonStatus | string;
  error: string | null;
  has_analysis: boolean;
}

export interface Evidence {
  source: "linkedin" | "instagram";
  quote: string;
}

export interface SayDoGap {
  stated: string;
  lived: string;
  type: "agree" | "diverge";
  evidence: Evidence[];
}

export interface Claim {
  claim: string;
  source: "linkedin" | "instagram" | "both";
  quote: string;
  kind: "stated" | "inferred";
  confidence: number;
}

export interface AnalysisPayload {
  summary: string;
  stated_self: { career: string; ambitions: string[]; presentation: string };
  lived_self: { hobbies: string[]; places: string[]; social_energy: string; aesthetic: string };
  say_do_gap: SayDoGap[];
  needs: string[];
  interests: string[];
  values: string[];
  personality: string[];
  communication_style: string;
  lifestyle: string;
  ambition_level: string;
  dating_intent: string;
  looking_for: string[];
  dealbreakers: string[];
  claims: Claim[];
  overall_confidence: number;
  data_gaps: string[];
}

export interface AnalysisOut {
  person_id: number;
  payload: AnalysisPayload;
  overall_confidence: number;
  verified_count: number;
  dropped_count: number;
  dropped: { kind?: string; claim?: string; quote?: string; reason?: string; stated?: string }[];
  embedding: number[] | null;
}

export interface PersonDetailOut extends PersonOut {
  linkedin_data: Record<string, unknown> | null;
  instagram_data: Record<string, unknown> | null;
  analysis: AnalysisOut | null;
}

export interface RunOut {
  id: number;
  status: string;
  error: string | null;
  stats: RunStats;
  started_at: string | null;
  finished_at: string | null;
}

export interface RunStats {
  phase?: string;
  total_people?: number;
  round1_total?: number;
  round1_done?: number;
  round1_failed?: number;
  round2_total?: number;
  round2_done?: number;
  round2_failed?: number;
  why_total?: number;
  why_done?: number;
  excluded?: { person_id: number; name: string; reason: string }[];
}

export interface TurnOut {
  idx: number;
  speaker_id: number;
  speaker_name: string;
  content: string;
}

export interface AgentScoreOut {
  person_id: number;
  person_name: string;
  score: number;
  chemistry: number;
  shared_interests: string[];
  friction: string[];
  would_meet_again: boolean;
  one_line_for_person: string | null;
}

export interface RefereeOut {
  chemistry: number;
  values_fit: number;
  lifestyle_fit: number;
  ambition_fit: number;
  interests_fit: number;
  tagged_turns: { turn_index: number; tag: "spark" | "friction"; reason: string }[];
}

export interface PairOut {
  date_id: number;
  round: number;
  person_a: number;
  person_b: number;
  person_a_name: string;
  person_b_name: string;
  scene: string | null;
  moderator_question: string | null;
  status: string;
  error: string | null;
  turns: TurnOut[];
  agent_scores: AgentScoreOut[];
  referee: RefereeOut | null;
}

export interface MatchBreakdown {
  values: number;
  interests: number;
  lifestyle: number;
  ambition: number;
  chemistry: number;
}

export interface BadgeTurnLink {
  turn_index: number;
  tag: string;
  reason: string;
}

export interface MatchOut {
  person_id: number;
  person_name: string;
  round_used: number;
  final: number;
  mutual: number;
  referee: number;
  embedding: number;
  breakdown: MatchBreakdown;
  why: string | null;
  similarity_rank: number;
  final_rank: number;
  delta: number;
  badge: string | null;
  badge_turn_link: BadgeTurnLink | null;
  pair_href: string;
  date_id: number;
}

export interface RankingOut {
  person: PersonOut;
  run_id: number | null;
  matches: MatchOut[];
  excluded: { person_id: number; name: string; reason: string }[];
}

export interface RankingsOverview {
  people: PersonOut[];
  run_id: number | null;
}

export interface ExportPerson {
  id: number;
  name: string;
  linkedin_url: string;
  instagram_url: string;
  status: string;
  error: string | null;
  linkedin_data: Record<string, unknown> | null;
  instagram_data: Record<string, unknown> | null;
  created_at?: string;
}

export interface ExportRun {
  id: number;
  status: string;
  error: string | null;
  stats: RunStats | null;
  started_at: string;
  finished_at: string | null;
}

export interface ExportDate {
  id: number;
  run_id: number;
  round: number;
  person_a: number;
  person_b: number;
  scene: string | null;
  moderator_question: string | null;
  status: string;
  error: string | null;
}

export interface ExportTurn {
  id: number;
  date_id: number;
  idx: number;
  speaker_id: number;
  content: string;
}

export interface ExportAgentScore {
  id: number;
  date_id: number;
  person_id: number;
  score: number;
  chemistry: number;
  shared_interests: string[] | null;
  friction: string[] | null;
  would_meet_again: boolean;
  one_line_for_person: string | null;
}

export interface ExportReferee {
  date_id: number;
  chemistry: number;
  values_fit: number;
  lifestyle_fit: number;
  ambition_fit: number;
  interests_fit: number;
  tagged_turns: { turn_index: number; tag: string; reason: string }[] | null;
}

export interface ExportPairScore {
  id: number;
  run_id: number;
  person_a: number;
  person_b: number;
  round_used: number;
  mutual: number;
  referee: number;
  embedding: number;
  final: number;
  why: string | null;
}

export interface ExportAnalysis {
  person_id: number;
  payload: AnalysisPayload;
  embedding: number[] | null;
  overall_confidence: number;
  verified_count: number;
  dropped_count: number;
  dropped: unknown[] | null;
}

export interface ExportData {
  version: number;
  exported_at: string;
  people: ExportPerson[];
  analyses: ExportAnalysis[];
  runs: ExportRun[];
  dates: ExportDate[];
  turns: ExportTurn[];
  agent_scores: ExportAgentScore[];
  referee_scores: ExportReferee[];
  pair_scores: ExportPairScore[];
}

export type SseEvent =
  | { type: "snapshot"; people: PersonOut[]; run: { id: number; status: string; stats: RunStats } | null; dates: { id: number; round: number; person_a: number; person_b: number; status: string; scene: string | null }[] }
  | { type: "person.status"; person_id: number; name: string; status: string; error?: string; confidence?: number }
  | { type: "run.progress"; run_id: number; stats: RunStats }
  | { type: "run.status"; run_id: number; status: string; stats?: RunStats; error?: string }
  | { type: "date.done"; date_id: number; round: number; person_a: number; person_b: number; person_a_name: string; person_b_name: string; status: string; scene?: string | null; error?: string; href?: string }
  | { type: "import.done"; people: number; analyses: number; runs: number };
