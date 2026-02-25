import { writable } from 'svelte/store';

export const wsConnected = writable<boolean>(false);
export const apiReachable = writable<boolean>(false);
