import { mount } from 'svelte';
import App from './App.svelte';
import './app.css';

const target = document.getElementById('blind-control-app');

if (!target) {
  throw new Error('Blind Control mount target is missing');
}

mount(App, { target });
