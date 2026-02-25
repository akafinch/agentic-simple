<script lang="ts">
	import type { HealthStatus } from '$lib/types';

	let expanded = $state(false);
	let health: HealthStatus | null = $state(null);
	let loading = $state(false);

	async function fetchHealth() {
		loading = true;
		try {
			const resp = await fetch('/api/health');
			health = await resp.json();
		} catch {
			health = null;
		} finally {
			loading = false;
		}
	}

	// Fetch on mount
	$effect(() => {
		fetchHealth();
	});
</script>

<div class="infra-panel">
	<button class="toggle" onclick={() => (expanded = !expanded)}>
		<span class="toggle-icon">{expanded ? '▾' : '▸'}</span>
		Infrastructure Status
		{#if health}
			<span class="status-dot" class:ok={health.status === 'ok'} class:degraded={health.status === 'degraded'} class:unavailable={health.status === 'unavailable'}></span>
			{#if health.mock_mode}
				<span class="mock-badge">MOCK</span>
			{/if}
		{/if}
	</button>

	{#if expanded}
		<div class="panel-body">
			{#if loading}
				<p class="loading">Checking infrastructure...</p>
			{:else if health}
				<div class="grid">
					<div class="card">
						<h4>Orchestrator (VM1)</h4>
						<div class="detail">
							<span class="label">Ollama</span>
							<span class:online={health.orchestrator.ollama} class:offline={!health.orchestrator.ollama}>
								{health.orchestrator.ollama ? 'Connected' : 'Unreachable'}
							</span>
						</div>
						<div class="detail">
							<span class="label">Model</span>
							<span>{health.orchestrator.model || health.orchestrator.models?.join(', ') || 'N/A'}</span>
						</div>
						<div class="detail">
							<span class="label">GPU</span>
							<span>RTX 6000 Pro (48GB)</span>
						</div>
					</div>

					<div class="card">
						<h4>Specialist (VM2)</h4>
						<div class="detail">
							<span class="label">Ollama</span>
							<span class:online={health.specialist.ollama} class:offline={!health.specialist.ollama}>
								{health.specialist.ollama ? 'Connected' : 'Unreachable'}
							</span>
						</div>
						<div class="detail">
							<span class="label">Model</span>
							<span>{health.specialist.model || health.specialist.models?.join(', ') || 'N/A'}</span>
						</div>
						<div class="detail">
							<span class="label">GPU</span>
							<span>RTX 4000 Ada (20GB)</span>
						</div>
					</div>
				</div>
			{:else}
				<p class="error">Failed to reach API</p>
			{/if}

			<button class="refresh" onclick={fetchHealth} disabled={loading}>
				Refresh
			</button>
		</div>
	{/if}
</div>

<style>
	.infra-panel {
		border-top: 1px solid var(--border);
	}

	.toggle {
		width: 100%;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1rem;
		background: none;
		border: none;
		color: var(--text-muted);
		font-size: 0.85rem;
		cursor: pointer;
		text-align: left;
	}

	.toggle:hover {
		color: var(--text);
	}

	.toggle-icon {
		font-size: 0.7rem;
	}

	.status-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}

	.status-dot.ok { background: var(--teal); }
	.status-dot.degraded { background: var(--amber); }
	.status-dot.unavailable { background: var(--red); }

	.mock-badge {
		background: var(--purple);
		color: white;
		font-size: 0.65rem;
		font-weight: 700;
		padding: 1px 6px;
		border-radius: 4px;
		letter-spacing: 0.05em;
	}

	.panel-body {
		padding: 0 1rem 1rem;
	}

	.grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin-bottom: 0.75rem;
	}

	.card {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 0.75rem;
	}

	.card h4 {
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--text);
		margin: 0 0 0.5rem;
	}

	.detail {
		display: flex;
		justify-content: space-between;
		font-size: 0.75rem;
		padding: 0.2rem 0;
	}

	.label {
		color: var(--gray-400);
	}

	.detail span:last-child {
		color: var(--text-muted);
	}

	.online { color: var(--teal) !important; }
	.offline { color: var(--red) !important; }

	.loading, .error {
		font-size: 0.85rem;
		color: var(--gray-400);
	}

	.error { color: var(--red); }

	.refresh {
		padding: 0.4rem 1rem;
		background: var(--surface-raised);
		border: 1px solid var(--border);
		border-radius: 6px;
		color: var(--text-muted);
		font-size: 0.8rem;
		cursor: pointer;
	}

	.refresh:hover:not(:disabled) {
		border-color: var(--blue);
		color: var(--text);
	}
</style>
