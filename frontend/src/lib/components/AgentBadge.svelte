<script lang="ts">
	import { AGENT_COLORS, AGENT_LABELS } from '$lib/types';

	let { agent }: { agent: string } = $props();

	let color = $derived(AGENT_COLORS[agent] || '#94A3B8');
	let label = $derived(AGENT_LABELS[agent] || agent);
</script>

<span class="badge" style="background: {color}; border: 1px solid {color}44;">
	{label}
</span>

<style>
	.badge {
		display: inline-block;
		padding: 2px 10px;
		border-radius: 12px;
		font-size: 0.75rem;
		font-weight: 600;
		color: #e2e8f0;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		white-space: nowrap;
	}
</style>
