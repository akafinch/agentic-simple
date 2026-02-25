import { writable, derived } from 'svelte/store';
import type { CrewEvent, RunStatus } from '$lib/types';

export const events = writable<CrewEvent[]>([]);
export const status = writable<RunStatus>('idle');
export const runId = writable<string | null>(null);
export const topic = writable<string>('');
export const reportMarkdown = writable<string | null>(null);
export const charts = writable<string[]>([]);
export const elapsedSeconds = writable<number>(0);
export const error = writable<string | null>(null);

export const currentAgent = derived(events, ($events) => {
	const last = [...$events].reverse().find((e) => e.type === 'agent_start');
	return last?.agent ?? null;
});

export const agentTimings = derived(events, ($events) => {
	const timings: Record<string, number> = {};
	for (const e of $events) {
		if (e.type === 'agent_complete' && e.agent && e.elapsed_seconds) {
			timings[e.agent] = e.elapsed_seconds;
		}
	}
	return timings;
});

export function resetCrew() {
	events.set([]);
	status.set('idle');
	runId.set(null);
	reportMarkdown.set(null);
	charts.set([]);
	elapsedSeconds.set(0);
	error.set(null);
}
