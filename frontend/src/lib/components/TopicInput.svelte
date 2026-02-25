<script lang="ts">
	import { PRESET_TOPICS } from '$lib/types';
	import { status, topic, resetCrew, runId, events, charts, reportMarkdown, error, elapsedSeconds } from '$lib/stores/crew';
	import { connectCrewStream } from '$lib/websocket';
	import type { CrewEvent } from '$lib/types';

	let inputValue = $state('');
	let isSubmitting = $state(false);
	let wsConnection: { close: () => void } | null = null;

	function handleEvent(event: CrewEvent) {
		events.update((e) => [...e, event]);

		if (event.type === 'chart_created' && event.path) {
			charts.update((c) => [...c, event.path!]);
		}

		if (event.type === 'crew_complete') {
			status.set('completed');
			if (event.total_seconds) elapsedSeconds.set(event.total_seconds);
			// Close the WebSocket — we have everything we need
			wsConnection?.close();
			wsConnection = null;
			// Fetch the full report
			fetchReport();
		}

		if (event.type === 'error' && !event.recoverable) {
			status.set('error');
			error.set(event.message || 'Unknown error');
			wsConnection?.close();
			wsConnection = null;
		}
	}

	async function fetchReport() {
		const id = $effect.tracking() ? null : null; // just need $runId
		// Use a small delay to ensure the report is written
		await new Promise((r) => setTimeout(r, 500));
		const currentRunId = getRunId();
		if (!currentRunId) return;
		try {
			const resp = await fetch(`/api/crew/report/${currentRunId}`);
			const data = await resp.json();
			if (data.report) {
				reportMarkdown.set(data.report);
			}
		} catch {
			// Report fetch failed — not critical
		}
	}

	let currentRunIdValue: string | null = null;
	runId.subscribe((v) => (currentRunIdValue = v));
	function getRunId() { return currentRunIdValue; }

	async function startRun() {
		if (!inputValue.trim() || isSubmitting) return;
		isSubmitting = true;
		resetCrew();
		topic.set(inputValue.trim());
		status.set('running');

		try {
			const resp = await fetch('/api/crew/run', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ topic: inputValue.trim() })
			});
			const data = await resp.json();
			runId.set(data.run_id);

			// Connect WebSocket for live events
			wsConnection = connectCrewStream(data.run_id, handleEvent, () => {
				// On close — if not already completed, fetch status
				if (getRunId()) fetchReport();
			});

			// Start elapsed timer
			startTimer();
		} catch (err) {
			status.set('error');
			error.set('Failed to start crew run');
		} finally {
			isSubmitting = false;
		}
	}

	function startTimer() {
		const start = Date.now();
		const interval = setInterval(() => {
			let currentStatus: string = 'running';
			status.subscribe((s) => (currentStatus = s))();
			if (currentStatus !== 'running') {
				clearInterval(interval);
				return;
			}
			elapsedSeconds.set(Math.round((Date.now() - start) / 1000));
		}, 1000);
	}

	function selectPreset(t: string) {
		inputValue = t;
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') startRun();
	}

	let isRunning = $derived($status === 'running');
</script>

<div class="topic-input">
	<div class="input-row">
		<input
			type="text"
			bind:value={inputValue}
			onkeydown={handleKeydown}
			placeholder="Enter a research topic..."
			disabled={isRunning}
		/>
		<button onclick={startRun} disabled={isRunning || !inputValue.trim()}>
			{#if isRunning}
				Running...
			{:else}
				Go
			{/if}
		</button>
	</div>

	<div class="presets">
		<span class="presets-label">Presets:</span>
		{#each PRESET_TOPICS as preset}
			<button class="preset-chip" onclick={() => selectPreset(preset)} disabled={isRunning}>
				{preset.length > 50 ? preset.slice(0, 50) + '...' : preset}
			</button>
		{/each}
	</div>
</div>

<style>
	.topic-input {
		width: 100%;
	}

	.input-row {
		display: flex;
		gap: 0.75rem;
	}

	input {
		flex: 1;
		padding: 0.75rem 1rem;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 8px;
		color: var(--text);
		font-size: 1rem;
		font-family: var(--font-sans);
		outline: none;
		transition: border-color 0.2s;
	}

	input:focus {
		border-color: var(--blue);
	}

	input:disabled {
		opacity: 0.5;
	}

	input::placeholder {
		color: var(--gray-400);
	}

	button {
		padding: 0.75rem 2rem;
		background: var(--blue);
		color: white;
		border: none;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.2s, opacity 0.2s;
		white-space: nowrap;
	}

	button:hover:not(:disabled) {
		background: #0085c0;
	}

	button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.presets {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.5rem;
		margin-top: 0.75rem;
	}

	.presets-label {
		font-size: 0.8rem;
		color: var(--gray-400);
	}

	.preset-chip {
		padding: 0.3rem 0.75rem;
		background: var(--surface-raised);
		border: 1px solid var(--border);
		border-radius: 16px;
		color: var(--text-muted);
		font-size: 0.75rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.preset-chip:hover:not(:disabled) {
		border-color: var(--blue);
		color: var(--text);
	}

	.preset-chip:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}
</style>
