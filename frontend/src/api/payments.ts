import { getJson, postJson } from './client';

export interface Billing {
  id: number;
  billing_id: string;
  order: number;
  order_id: string;
  customer: number;
  customer_external_id: string;
  payment_url: string;
  amount: string;
  status: 'PENDING' | 'PAID' | 'EXPIRED' | 'CANCELLED';
  methods: string[];
  frequency: string;
  dev_mode: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateBillingRequest {
  order_id: string;
  description?: string;
  metadata?: Record<string, any>;
}

// POST /payments/billing/create/ - Create billing for an order
export async function createBilling(data: CreateBillingRequest): Promise<Billing> {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  return postJson<Billing>('/payments/billing/create/', data, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

// GET /payments/billing/{billing_id}/status/ - Get billing status
export async function getBillingStatus(billingId: string): Promise<{
  billing_id: string;
  status: string;
  amount: string;
  payment_url?: string;
  methods?: string[];
}> {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  return getJson(`/payments/billing/${billingId}/status/`, undefined, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}
