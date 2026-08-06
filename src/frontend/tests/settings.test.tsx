import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { SettingsPage } from '../src/pages/SettingsPage';
import { healthResponse, jsonResponse, renderWithClient } from './testUtils';


describe('Frontend preferences', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
    document.documentElement.removeAttribute('data-text-size');
    document.documentElement.removeAttribute('data-font-style');
    vi.stubGlobal('fetch', vi.fn(() => jsonResponse(healthResponse)));
  });
  afterEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
    document.documentElement.removeAttribute('data-text-size');
    document.documentElement.removeAttribute('data-font-style');
  });

  it('stays in English and persists appearance preferences', async () => {
    localStorage.setItem('lain5g.preferences.v1', JSON.stringify({ language: 'es' }));
    renderWithClient(<SettingsPage />);
    expect(await screen.findByRole('heading', { name: 'Settings' })).toBeInTheDocument();
    await waitFor(() => expect(document.documentElement).toHaveAttribute('data-theme', 'light'));
    expect(screen.queryByRole('button', { name: 'Spanish' })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Dark' }));
    await userEvent.click(screen.getByRole('button', { name: 'Large' }));
    await userEvent.click(screen.getByRole('button', { name: 'Technical' }));

    await waitFor(() => {
      expect(document.documentElement).toHaveAttribute('lang', 'en');
      expect(document.documentElement).toHaveAttribute('data-theme', 'dark');
      expect(document.documentElement).toHaveAttribute('data-text-size', 'large');
      expect(document.documentElement).toHaveAttribute('data-font-style', 'technical');
    });
    const stored = JSON.parse(localStorage.getItem('lain5g.preferences.v1') || '{}');
    expect(stored).not.toHaveProperty('language');
    expect(stored).toMatchObject({ theme: 'dark', textSize: 'large', fontStyle: 'technical' });
  });
});
