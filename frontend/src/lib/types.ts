export interface CrewEvent {
	type:
		| 'agent_start'
		| 'agent_output'
		| 'agent_complete'
		| 'delegation'
		| 'chart_created'
		| 'crew_complete'
		| 'error';
	timestamp: string;
	run_id?: string;
	agent?: string;
	role?: string;
	model?: string;
	vm?: string;
	task_summary?: string;
	content?: string;
	from?: string;
	to?: string;
	instruction?: string;
	chart_title?: string;
	path?: string;
	elapsed_seconds?: number;
	total_seconds?: number;
	report_path?: string;
	charts?: string[];
	message?: string;
	recoverable?: boolean;
}

export interface CrewStatus {
	run_id: string;
	topic: string;
	status: 'pending' | 'running' | 'completed' | 'error';
	elapsed_seconds: number | null;
	events_count: number;
	report_path: string | null;
	charts: string[];
	error: string | null;
}

export interface HealthStatus {
	status: 'ok' | 'degraded' | 'unavailable';
	mock_mode: boolean;
	orchestrator: {
		ollama: boolean;
		model?: string;
		models?: string[];
	};
	specialist: {
		ollama: boolean;
		model?: string;
		models?: string[];
	};
}

export interface WarmupResult {
	orchestrator_ms: number;
	specialist_ms: number;
	mock_mode?: boolean;
}

export type RunStatus = 'idle' | 'running' | 'completed' | 'error';

export const AGENT_COLORS: Record<string, string> = {
	manager: '#0D1B2A',
	researcher: '#009BDE',
	analyst: '#00D4AA',
	visualizer: '#6366F1',
	writer: '#EAB308',
	system: '#EF4444'
};

export const AGENT_LABELS: Record<string, string> = {
	manager: 'Manager',
	researcher: 'Researcher',
	analyst: 'Analyst',
	visualizer: 'Visualizer',
	writer: 'Writer',
	system: 'System'
};

export const PRESET_TOPICS = [
	'Analyze the competitive landscape for edge AI inference providers in 2025',
	'Compare GPU cloud providers for machine learning inference workloads',
	'Evaluate the market opportunity for AI-powered content moderation at the network edge',
	'Assess the impact of on-device AI vs cloud AI for real-time video analytics'
];
