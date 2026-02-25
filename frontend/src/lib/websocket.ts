import type { CrewEvent } from './types';

interface StreamConnection {
	close: () => void;
}

export function connectCrewStream(
	runId: string,
	onEvent: (event: CrewEvent) => void,
	onClose?: () => void
): StreamConnection {
	const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
	const url = `${protocol}//${location.host}/ws/crew/stream/${runId}`;
	let ws: WebSocket | null = null;
	let reconnectAttempts = 0;
	let closed = false;

	function connect() {
		ws = new WebSocket(url);

		ws.onopen = () => {
			reconnectAttempts = 0;
		};

		ws.onmessage = (msg) => {
			try {
				const event: CrewEvent = JSON.parse(msg.data);
				onEvent(event);
			} catch {
				// Ignore malformed messages
			}
		};

		ws.onclose = (event) => {
			// Don't reconnect on clean close (server signals run complete)
			if (closed || event.code === 1000) {
				onClose?.();
				return;
			}
			// Reconnect with exponential backoff (max 10s)
			const delay = Math.min(1000 * 2 ** reconnectAttempts, 10000);
			reconnectAttempts++;
			if (reconnectAttempts <= 5) {
				setTimeout(connect, delay);
			} else {
				onClose?.();
			}
		};

		ws.onerror = () => {
			ws?.close();
		};
	}

	connect();

	return {
		close() {
			closed = true;
			ws?.close();
		}
	};
}
