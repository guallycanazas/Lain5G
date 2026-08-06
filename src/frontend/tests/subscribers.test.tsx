import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SubscriberCreatePage } from '../src/pages/SubscriberCreatePage';
import { SubscriberEditPage } from '../src/pages/SubscriberEditPage';
import { SubscribersPage } from '../src/pages/SubscribersPage';
import { jsonResponse, renderRoute, renderWithClient, subscriberConnection, subscriberDetail, subscriberList } from './testUtils';

describe('Subscriber management', () => {
  beforeEach(() => vi.restoreAllMocks());

  it('shows MongoDB connection and subscriber list without secrets', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if (url.includes('/connection')) return jsonResponse(subscriberConnection);
      if (url.includes('/api/subscribers?')) return jsonResponse(subscriberList);
      return jsonResponse({});
    }));

    renderWithClient(<SubscribersPage />);

    expect(await screen.findByText('mongo:27017')).toBeInTheDocument();
    expect(await screen.findByText('001010000000001')).toBeInTheDocument();
    expect(screen.getByText('51999999999')).toBeInTheDocument();
    expect(document.body.textContent).not.toContain('001122334455');
  });

  it('shows empty state and MongoDB errors', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if (url.includes('/connection')) return jsonResponse({ ...subscriberConnection, status: 'disconnected', message: 'MongoDB is not available' });
      if (url.includes('/api/subscribers?')) return jsonResponse({ detail: { code: 'SUBSCRIBER_MONGO_UNAVAILABLE', message: 'MongoDB is not available.' } }, 503);
      return jsonResponse({});
    }));

    renderWithClient(<SubscribersPage />);

    expect(await screen.findByText('MongoDB is not available.')).toBeInTheDocument();
  });

  it('searches subscribers', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if (url.includes('/connection')) return jsonResponse(subscriberConnection);
      return jsonResponse(subscriberList);
    }));

    renderWithClient(<SubscribersPage />);
    await userEvent.type(await screen.findByLabelText('Search IMSI / MSISDN'), '001010');
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringContaining('search=001010'), expect.any(Object)));
  });

  it('validates form fields before creation', async () => {
    vi.stubGlobal('fetch', vi.fn(() => jsonResponse({})));
    renderWithClient(<SubscriberCreatePage />);

    await userEvent.click(screen.getByRole('button', { name: 'Create subscriber' }));

    expect(await screen.findByText('IMSI must contain 5 to 15 digits.')).toBeInTheDocument();
    expect(screen.getByText('K must contain 32 hexadecimal characters.')).toBeInTheDocument();
  });

  it('creates a valid subscriber and disables button while sending', async () => {
    vi.stubGlobal('fetch', vi.fn(() => jsonResponse({ subscriber: subscriberDetail, dry_run: false, persisted: true, message: 'created' }, 201)));
    renderWithClient(<SubscriberCreatePage />);

    await userEvent.type(screen.getByLabelText('IMSI *'), '001010000000010');
    await userEvent.type(screen.getByLabelText('MSISDN'), '51999999991');
    await userEvent.type(screen.getByLabelText('K *'), '00112233445566778899aabbccddeeff');
    await userEvent.type(screen.getByLabelText('OPc'), 'ffeeddccbbaa99887766554433221100');
    await userEvent.click(screen.getByRole('button', { name: 'Create subscriber' }));

    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/subscribers', expect.objectContaining({ method: 'POST' })));
  });

  it('edits while keeping secrets empty', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string, init?: RequestInit) => {
      if (init?.method === 'PATCH') return jsonResponse({ subscriber: { ...subscriberDetail, msisdn: '51888888888' }, dry_run: false, persisted: true, message: 'updated' });
      return jsonResponse(subscriberDetail);
    }));

    renderRoute('/subscribers/:imsi/edit', <SubscriberEditPage />, '/subscribers/001010000000001/edit');
    await userEvent.clear(await screen.findByLabelText('MSISDN'));
    await userEvent.type(screen.getByLabelText('MSISDN'), '51888888888');
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }));

    await waitFor(() => {
      const [, init] = vi.mocked(fetch).mock.calls.find(([url, request]) => String(url).includes('/api/subscribers/001010000000001') && request?.method === 'PATCH')!;
      expect(String(init?.body)).not.toContain('001122334455');
    });
  });

  it('clones and deletes with confirmation', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string, init?: RequestInit) => {
      if (url.includes('/connection')) return jsonResponse(subscriberConnection);
      if (url.includes('/clone')) return jsonResponse({ subscriber: { ...subscriberDetail, imsi: '001010000000002' }, dry_run: false, persisted: true, message: 'cloned' }, 201);
      if (init?.method === 'DELETE') return jsonResponse({ dry_run: false, persisted: true, message: 'deleted' });
      return jsonResponse(subscriberList);
    }));

    renderWithClient(<SubscribersPage />);
    await userEvent.click((await screen.findAllByRole('button', { name: 'Clone' }))[0]);
    await userEvent.type(screen.getByLabelText('New IMSI'), '001010000000002');
    await userEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Clone' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/subscribers/001010000000001/clone', expect.objectContaining({ method: 'POST' })));

    await userEvent.click((await screen.findAllByRole('button', { name: 'Delete' }))[0]);
    await userEvent.type(screen.getByLabelText('Confirm IMSI'), '001010000000001');
    await userEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Delete' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/subscribers/001010000000001', expect.objectContaining({ method: 'DELETE' })));
  });
});
