import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, expect, test } from 'vitest';
import LLMUsage from '../src/LLMUsage';
import type { Frame } from '../src/types';
import { createWorkbenchFixture } from './fixtures/workbench.mock';

afterEach(cleanup);

function usageFrame(): Frame {
  const frame: Frame = createWorkbenchFixture().frame;
  frame.cognition = {
    provider: 'ollama', is_llm: true, calls: 7, charged_tokens: 900,
    per_actor_usage: { Red_0: { charged_tokens: 120 }, Red_1: { charged_tokens: 330 }, Coordinator: { charged_tokens: 450 } },
  };
  return frame;
}

test('researcher sees recorded team calls and accounting, without claiming measured tokens', () => {
  const frame = usageFrame();
  const original = structuredClone(frame);
  render(<LLMUsage frame={frame} view="truth"/>);
  expect(screen.getByText('TEAM ACCOUNTED TOKENS')).toBeTruthy();
  expect(screen.getByText('900', { exact: true })).toBeTruthy();
  expect(screen.getByText('LLM calls: 7')).toBeTruthy();
  expect(screen.getByText('Saved frame team total, including worker, coordinator and repair calls when used.')).toBeTruthy();
  expect(screen.getByText(/Accounted tokens may include budget reservations/)).toBeTruthy();
  expect(screen.getByText(/A measured\/reserved breakdown is not available/)).toBeTruthy();
  expect(frame).toEqual(original);
});

test.each([true, false])('recorded zero remains zero (LLM mode: %s)', is_llm => {
  const frame = usageFrame();
  frame.cognition = { is_llm, provider: is_llm ? 'ollama' : 'scripted', calls: 0, charged_tokens: 0 };
  render(<LLMUsage frame={frame} view="truth"/>);
  expect(screen.getByText('0', { exact: true })).toBeTruthy();
  expect(screen.getByText('LLM calls: 0')).toBeTruthy();
});

test('missing saved usage fields are not fabricated as zero', () => {
  const frame = usageFrame();
  // Historical/incomplete JSON can omit fields even though current types require them.
  Reflect.deleteProperty(frame.cognition, 'calls');
  Reflect.deleteProperty(frame.cognition, 'charged_tokens');
  const { rerender } = render(<LLMUsage frame={frame} view="truth"/>);
  expect(screen.getByText('Not recorded', { exact: true })).toBeTruthy();
  expect(screen.getByText('LLM calls: Not recorded')).toBeTruthy();
  expect(screen.queryByText('0', { exact: true })).toBeNull();
  rerender(<LLMUsage frame={null} view="truth"/>);
  expect(screen.getByText('LLM calls: Not recorded')).toBeTruthy();
});

test('private views show only own accounting and never fall back to team or peer data', () => {
  const frame = usageFrame();
  const { rerender } = render(<LLMUsage frame={frame} view="truth"/>);
  expect(screen.getByText('LLM calls: 7')).toBeTruthy();
  rerender(<LLMUsage frame={frame} view="Red_0"/>);
  expect(screen.getByText('OWN ACCOUNTED TOKENS')).toBeTruthy();
  expect(screen.getByText('120', { exact: true })).toBeTruthy();
  for (const hidden of ['900', '330', '450', 'LLM calls: 7']) expect(screen.queryByText(hidden, { exact: true })).toBeNull();
  expect(document.body.textContent).not.toContain('TEAM ACCOUNTED TOKENS');
  rerender(<LLMUsage frame={frame} view="Red_1"/>);
  expect(screen.getByText('330', { exact: true })).toBeTruthy();
  expect(screen.queryByText('120', { exact: true })).toBeNull();
  delete frame.cognition.per_actor_usage;
  rerender(<LLMUsage frame={frame} view="Red_0"/>);
  expect(screen.getByText('Not recorded', { exact: true })).toBeTruthy();
  expect(screen.queryByText('900', { exact: true })).toBeNull();
});

test('own recorded zero is preserved in LLM mode', () => {
  const frame = usageFrame();
  frame.cognition.per_actor_usage!.Red_0.charged_tokens = 0;
  render(<LLMUsage frame={frame} view="Red_0"/>);
  expect(screen.getByText('0', { exact: true })).toBeTruthy();
  expect(document.body.textContent).not.toContain('LLM calls:');
});
