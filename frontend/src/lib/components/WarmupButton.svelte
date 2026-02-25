<script lang="ts">
	import type { WarmupResult } from '$lib/types';

	let loading = $state(false);
	let result: WarmupResult | null = $state(null);
	let error: string | null = $state(null);

	async function warmup() {
		loading = true;
		error = null;
		result = null;
		try {
			const resp = await fetch('/api/warmup', { method: 'POST' });
			result = await resp.json();
		} catch {
			error = 'Failed to reach API';
		} finally {
			loading = false;
		}
	}
</script>

<div class="warmup">
	<button onclick={warmup} disabled={loading}>
		{#if loading}
			Warming up...
		{:else}
			Warmup Models
		{/if}
	</button>

	{#if result}
		<div class="result">
			{#if result.mock_mode}
				<span class="mock">Mock mode — instant</span>
			{:else}
				<span>Orchestrator: {result.orchestrator_ms}ms</span>
				<span>Specialist: {result.specialist_ms}ms</span>
			{/if}
		</div>
	{/if}

	{#if error}
		<div class="error">{error}</div>
	{/if}
</div>

<style>
	.warmup {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	button {
		padding: 0.4rem 1rem;
		background: var(--surface-raised);
		border: 1px solid var(--border);
		border-radius: 6px;
		color: var(--text-muted);
		font-size: 0.8rem;
		cursor: pointer;
		white-space: nowrap;
		transition: all 0.2s;
	}

	button:hover:not(:disabled) {
		border-color: var(--teal);
		color: var(--teal);
	}

	button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.result {
		display: flex;
		gap: 1rem;
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--teal);
	}

	.mock {
		color: var(--purple);
	}

	.error {
		font-size: 0.75rem;
		color: var(--red);
	}
</style>
