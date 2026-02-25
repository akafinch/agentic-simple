<script lang="ts">
	import { status, elapsedSeconds, agentTimings, currentAgent } from '$lib/stores/crew';
	import { AGENT_COLORS, AGENT_LABELS } from '$lib/types';

	function formatTime(seconds: number): string {
		const m = Math.floor(seconds / 60);
		const s = seconds % 60;
		return m > 0 ? `${m}m ${s}s` : `${s}s`;
	}
</script>

{#if $status !== 'idle'}
	<div class="timer">
		<div class="elapsed">
			<span class="timer-label">
				{$status === 'running' ? 'Elapsed' : 'Total'}
			</span>
			<span class="timer-value">{formatTime($elapsedSeconds)}</span>
			{#if $status === 'running' && $currentAgent}
				<span class="current-agent" style="color: {AGENT_COLORS[$currentAgent] || '#94A3B8'}">
					{AGENT_LABELS[$currentAgent] || $currentAgent} working...
				</span>
			{/if}
		</div>

		{#if Object.keys($agentTimings).length > 0}
			<div class="breakdown">
				{#each Object.entries($agentTimings) as [agent, secs]}
					<span class="agent-time" style="color: {AGENT_COLORS[agent] || '#94A3B8'}">
						{AGENT_LABELS[agent] || agent}: {secs}s
					</span>
				{/each}
			</div>
		{/if}
	</div>
{/if}

<style>
	.timer {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: 0.75rem;
		padding: 0.5rem 0;
	}

	.elapsed {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.timer-label {
		font-size: 0.8rem;
		color: var(--gray-400);
	}

	.timer-value {
		font-family: var(--font-mono);
		font-size: 1.1rem;
		font-weight: 600;
		color: var(--text);
	}

	.current-agent {
		font-size: 0.8rem;
		font-style: italic;
	}

	.breakdown {
		display: flex;
		gap: 1rem;
	}

	.agent-time {
		font-family: var(--font-mono);
		font-size: 0.75rem;
	}
</style>
