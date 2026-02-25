<script lang="ts">
	import { marked } from 'marked';
	import { reportMarkdown, status, charts } from '$lib/stores/crew';
	import ChartImage from './ChartImage.svelte';

	// Rewrite relative image paths to /output/ so the backend serves them
	const renderer = new marked.Renderer();
	const originalImage = renderer.image.bind(renderer);
	renderer.image = function ({ href, title, text }) {
		// ./charts/foo.png → /output/charts/foo.png
		if (href && !href.startsWith('http') && !href.startsWith('/output')) {
			href = '/output/' + href.replace(/^\.\//, '');
		}
		return `<img src="${href}" alt="${text || ''}" title="${title || ''}" />`;
	};

	function cleanMarkdown(md: string): string {
		let cleaned = md.trim();

		// Strip "Thought: ..." preamble before the actual markdown heading
		const headingIdx = cleaned.search(/^#/m);
		if (headingIdx > 0 && cleaned.startsWith('Thought:')) {
			cleaned = cleaned.slice(headingIdx).trim();
		}

		// Strip ```markdown ... ``` wrapping that LLMs sometimes add
		if (cleaned.startsWith('```markdown')) {
			cleaned = cleaned.slice('```markdown'.length).trim();
		} else if (cleaned.startsWith('```md')) {
			cleaned = cleaned.slice('```md'.length).trim();
		} else if (cleaned.startsWith('```') && !cleaned.startsWith('```\n#')) {
			cleaned = cleaned.slice(3).trim();
		}
		if (cleaned.endsWith('```')) {
			cleaned = cleaned.slice(0, -3).trim();
		}
		return cleaned;
	}

	let renderedHtml = $derived(
		$reportMarkdown ? marked.parse(cleanMarkdown($reportMarkdown), { renderer, async: false }) as string : ''
	);

	let chartPaths = $derived($charts);
</script>

<div class="report-view">
	<div class="report-header">
		<h3>Report</h3>
	</div>

	<div class="report-content">
		{#if $status === 'idle'}
			<div class="empty">
				<div class="empty-icon">📊</div>
				<p>Select a research topic and click <strong>Go</strong> to start.</p>
				<p class="empty-sub">The crew will research, analyze, visualize, and write a report.</p>
			</div>
		{:else if $status === 'running' && !$reportMarkdown}
			<div class="generating">
				<div class="spinner"></div>
				<p>Agents are working...</p>
				{#if chartPaths.length > 0}
					<div class="preview-charts">
						<h4>Charts generated so far:</h4>
						{#each chartPaths as path}
							<ChartImage src={path} />
						{/each}
					</div>
				{/if}
			</div>
		{:else if $reportMarkdown}
			<article class="markdown-body">
				{@html renderedHtml}
			</article>
		{:else if $status === 'error'}
			<div class="error-state">
				<p>Something went wrong. Check the agent log for details.</p>
			</div>
		{/if}
	</div>
</div>

<style>
	.report-view {
		display: flex;
		flex-direction: column;
		height: 100%;
		min-height: 0;
	}

	.report-header {
		padding: 0.75rem 1rem;
		border-bottom: 1px solid var(--border);
	}

	.report-header h3 {
		font-size: 0.9rem;
		font-weight: 600;
		color: var(--text);
		margin: 0;
	}

	.report-content {
		flex: 1;
		overflow-y: auto;
		padding: 1.5rem;
	}

	.empty, .generating {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 300px;
		text-align: center;
		color: var(--gray-400);
	}

	.empty-icon {
		font-size: 3rem;
		margin-bottom: 1rem;
	}

	.empty p {
		margin: 0.25rem 0;
	}

	.empty-sub {
		font-size: 0.85rem;
		color: var(--gray-500);
	}

	.spinner {
		width: 32px;
		height: 32px;
		border: 3px solid var(--border);
		border-top-color: var(--blue);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
		margin-bottom: 1rem;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.preview-charts {
		margin-top: 1.5rem;
		width: 100%;
		max-width: 600px;
	}

	.preview-charts h4 {
		font-size: 0.85rem;
		color: var(--text-muted);
		margin-bottom: 0.75rem;
	}

	.error-state {
		text-align: center;
		color: var(--red);
		padding: 3rem;
	}

	/* Markdown body styles */
	.markdown-body {
		color: var(--text);
		line-height: 1.7;
	}

	.markdown-body :global(h1) {
		font-size: 1.8rem;
		font-weight: 700;
		color: var(--text);
		margin: 0 0 1rem;
		padding-bottom: 0.5rem;
		border-bottom: 2px solid var(--border);
	}

	.markdown-body :global(h2) {
		font-size: 1.3rem;
		font-weight: 600;
		color: var(--blue);
		margin: 2rem 0 0.75rem;
	}

	.markdown-body :global(h3) {
		font-size: 1.1rem;
		font-weight: 600;
		color: var(--teal);
		margin: 1.5rem 0 0.5rem;
	}

	.markdown-body :global(h4) {
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-muted);
		margin: 1rem 0 0.5rem;
	}

	.markdown-body :global(p) {
		margin: 0.75rem 0;
	}

	.markdown-body :global(strong) {
		color: var(--text);
		font-weight: 600;
	}

	.markdown-body :global(ul), .markdown-body :global(ol) {
		padding-left: 1.5rem;
		margin: 0.5rem 0;
	}

	.markdown-body :global(li) {
		margin: 0.25rem 0;
	}

	.markdown-body :global(hr) {
		border: none;
		border-top: 1px solid var(--border);
		margin: 2rem 0;
	}

	.markdown-body :global(code) {
		background: var(--surface-raised);
		padding: 0.15rem 0.4rem;
		border-radius: 4px;
		font-size: 0.9em;
	}

	.markdown-body :global(pre) {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 1rem;
		overflow-x: auto;
	}

	.markdown-body :global(img) {
		max-width: 100%;
		border-radius: 8px;
		border: 1px solid var(--border);
		margin: 1rem 0;
	}

	.markdown-body :global(blockquote) {
		border-left: 3px solid var(--blue);
		padding-left: 1rem;
		color: var(--text-muted);
		margin: 1rem 0;
	}

	.markdown-body :global(em) {
		color: var(--text-muted);
	}
</style>
