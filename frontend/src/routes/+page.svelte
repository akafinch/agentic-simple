<script lang="ts">
	import TopicInput from '$lib/components/TopicInput.svelte';
	import AgentLog from '$lib/components/AgentLog.svelte';
	import ReportView from '$lib/components/ReportView.svelte';
	import Timer from '$lib/components/Timer.svelte';
	import InfraPanel from '$lib/components/InfraPanel.svelte';
	import WarmupButton from '$lib/components/WarmupButton.svelte';
	import { status } from '$lib/stores/crew';
</script>

<div class="app">
	<!-- Header -->
	<header>
		<div class="header-left">
			<h1>Akamai <span class="accent">Edge AI</span> Market Analyst</h1>
			<span class="subtitle">Multi-Agent Research System</span>
		</div>
		<div class="header-right">
			<WarmupButton />
		</div>
	</header>

	<!-- Topic Input -->
	<section class="input-section">
		<TopicInput />
		<Timer />
	</section>

	<!-- Main Content: Two-column layout -->
	<main>
		<div class="col-log">
			<AgentLog />
		</div>
		<div class="col-report">
			<ReportView />
		</div>
	</main>

	<!-- Infrastructure Panel -->
	<footer>
		<InfraPanel />
	</footer>
</div>

<style>
	.app {
		display: flex;
		flex-direction: column;
		height: 100vh;
		max-height: 100vh;
		overflow: hidden;
	}

	/* ── Header ── */
	header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem 1.5rem;
		background: var(--navy-light);
		border-bottom: 1px solid var(--border);
		flex-shrink: 0;
	}

	.header-left {
		display: flex;
		align-items: baseline;
		gap: 1rem;
	}

	h1 {
		font-size: 1.2rem;
		font-weight: 700;
		color: var(--text);
		margin: 0;
	}

	.accent {
		color: var(--blue);
	}

	.subtitle {
		font-size: 0.8rem;
		color: var(--gray-400);
	}

	.header-right {
		flex-shrink: 0;
	}

	/* ── Input Section ── */
	.input-section {
		padding: 1rem 1.5rem;
		border-bottom: 1px solid var(--border);
		flex-shrink: 0;
	}

	/* ── Main Content ── */
	main {
		flex: 1;
		display: flex;
		min-height: 0;
	}

	.col-log {
		width: 40%;
		min-width: 300px;
		border-right: 1px solid var(--border);
		display: flex;
		flex-direction: column;
		min-height: 0;
	}

	.col-report {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-height: 0;
	}

	/* ── Footer ── */
	footer {
		flex-shrink: 0;
	}

	/* ── Responsive ── */
	@media (max-width: 768px) {
		main {
			flex-direction: column;
		}

		.col-log {
			width: 100%;
			max-height: 40vh;
			border-right: none;
			border-bottom: 1px solid var(--border);
		}
	}
</style>
