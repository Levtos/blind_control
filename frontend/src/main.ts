import { mount } from 'svelte';
import Shell from './Shell.svelte';
import './app.css';

const target = document.getElementById('blind-control-app');

if (!target) {
  throw new Error('Blind Control mount target is missing');
}

mount(Shell, { target });
