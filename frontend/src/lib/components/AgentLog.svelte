<script lang="ts">
	import { events, status } from '$lib/stores/crew';
	import AgentBadge from './AgentBadge.svelte';
	import type { CrewEvent } from '$lib/types';

	let logEl: HTMLDivElement | undefined = $state();
	let autoScroll = $state(true);

	function handleScroll() {
		if (!logEl) return;
		const { scrollTop, scrollHeight, clientHeight } = logEl;
		autoScroll = scrollHeight - scrollTop - clientHeight < 60;
	}

	$effect(() => {
		// Re-run whenever events change
		$events;
		if (autoScroll && logEl) {
			requestAnimationFrame(() => {
				logEl!.scrollTop = logEl!.scrollHeight;
			});
		}
	});

	function formatTime(ts: string): string {
		try {
			return new Date(ts).toLocaleTimeString('en-US', { hour12: false });
		} catch {
			return '';
		}
	}

	function eventSummary(e: CrewEvent): string {
		switch (e.type) {
			case 'agent_start':
				return `Starting: ${e.task_summary || e.role || 'working...'}`;
			case 'agent_output': {
				const content = e.content || '';
				// Truncate long outputs for the log display
				if (content.length > 500) {
					return content.slice(0, 500) + '...';
				}
				return content;
			}
			case 'tool_use':
				return `Using tool: ${e.tool || 'unknown'}`;
			case 'agent_complete':
				return `Completed (${e.elapsed_seconds}s)`;
			case 'delegation':
				return `Delegating to ${e.to}: ${e.instruction || ''}`;
			case 'chart_created':
				return `Chart created: ${e.chart_title}`;
			case 'crew_complete':
				return `Crew complete — ${e.total_seconds}s total`;
			case 'error':
				return `Error: ${e.message}`;
			default:
				return JSON.stringify(e);
		}
	}

	function eventAgent(e: CrewEvent): string {
		if (e.type === 'delegation') return e.from || 'manager';
		return e.agent || 'system';
	}
</script>

<div class="agent-log">
	<div class="log-header">
		<h3>Agent Activity</h3>
		{#if $status === 'running'}
			<span class="live-dot"></span>
		{/if}
	</div>

	<div class="log-entries" bind:this={logEl} onscroll={handleScroll}>
		{#if $events.length === 0}
			<div class="empty">Waiting for a crew run to start...</div>
		{/if}

		{#each $events as event, i (i)}
			<div class="log-entry" class:is-error={event.type === 'error'} class:is-complete={event.type === 'crew_complete'}>
				<div class="entry-header">
					<span class="timestamp">{formatTime(event.timestamp)}</span>
					<AgentBadge agent={eventAgent(event)} />
					{#if event.type === 'delegation'}
						<span class="arrow">→</span>
						<AgentBadge agent={event.to || 'unknown'} />
					{/if}
				</div>
				<div class="entry-content">
					{eventSummary(event)}
				</div>
			</div>
		{/each}
	</div>
</div>

<style>
	.agent-log {
		display: flex;
		flex-direction: column;
		height: 100%;
		min-height: 0;
	}

	.log-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1rem;
		border-bottom: 1px solid var(--border);
	}

	.log-header h3 {
		font-size: 0.9rem;
		font-weight: 600;
		color: var(--text);
		margin: 0;
	}

	.live-dot {
		width: 8px;
		height: 8px;
		background: var(--teal);
		border-radius: 50%;
		animation: pulse 1.5s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.3; }
	}

	.log-entries {
		flex: 1;
		overflow-y: auto;
		padding: 0.5rem;
	}

	.empty {
		padding: 2rem;
		text-align: center;
		color: var(--gray-400);
		font-size: 0.9rem;
	}

	.log-entry {
		padding: 0.5rem 0.75rem;
		border-radius: 6px;
		margin-bottom: 0.25rem;
		transition: background 0.2s;
	}

	.log-entry:hover {
		background: var(--surface-raised);
	}

	.log-entry.is-error {
		border-left: 3px solid var(--red);
	}

	.log-entry.is-complete {
		border-left: 3px solid var(--teal);
	}

	.entry-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.25rem;
	}

	.timestamp {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		color: var(--gray-400);
	}

	.arrow {
		color: var(--gray-300);
		font-size: 0.8rem;
	}

	.entry-content {
		font-size: 0.85rem;
		color: var(--text-muted);
		line-height: 1.5;
		white-space: pre-wrap;
		word-break: break-word;
	}
</style>
