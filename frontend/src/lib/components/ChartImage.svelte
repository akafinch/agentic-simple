<script lang="ts">
	let { src, title = '' }: { src: string; title?: string } = $props();
	let loaded = $state(false);
	let errored = $state(false);
</script>

<div class="chart-container">
	{#if !loaded && !errored}
		<div class="skeleton">
			<div class="skeleton-pulse"></div>
			<span>Generating chart...</span>
		</div>
	{/if}

	{#if errored}
		<div class="error">Failed to load chart</div>
	{/if}

	<img
		{src}
		alt={title}
		class:hidden={!loaded}
		onload={() => (loaded = true)}
		onerror={() => (errored = true)}
	/>
</div>

<style>
	.chart-container {
		width: 100%;
		border-radius: 8px;
		overflow: hidden;
		background: var(--surface);
		border: 1px solid var(--border);
	}

	img {
		width: 100%;
		height: auto;
		display: block;
	}

	img.hidden {
		display: none;
	}

	.skeleton {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 200px;
		gap: 0.75rem;
		color: var(--gray-400);
		font-size: 0.85rem;
	}

	.skeleton-pulse {
		width: 60%;
		height: 8px;
		background: var(--surface-raised);
		border-radius: 4px;
		animation: shimmer 1.5s ease-in-out infinite;
	}

	@keyframes shimmer {
		0%, 100% { opacity: 0.3; }
		50% { opacity: 0.7; }
	}

	.error {
		padding: 2rem;
		text-align: center;
		color: var(--red);
		font-size: 0.85rem;
	}
</style>
