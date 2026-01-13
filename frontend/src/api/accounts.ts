import { getJson, postJson, putJson, patchJson } from './client';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  cpf?: string;
  telefone?: string;
  data_nascimento?: string;
  nick_habbo?: string;
  habbo_validado?: boolean;
  wallet_address?: string;
  created_at: string;
  updated_at: string;
}

export interface AuthMessageResponse {
  message: string;
}

export interface MetaMaskAuthRequest {
  wallet_address: string;
  signature: string;
  message: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
  is_new_user: boolean;
}

// GET /accounts/auth/metamask/message/ - Generate auth message
export function generateAuthMessage(walletAddress: string) {
  return getJson<AuthMessageResponse>('/accounts/auth/metamask/message/', {
    wallet_address: walletAddress,
  });
}

// POST /accounts/auth/metamask/login/ - Login with MetaMask
export function loginWithMetaMask(data: MetaMaskAuthRequest) {
  return postJson<AuthResponse>('/accounts/auth/metamask/login/', data);
}

// GET /accounts/me/ - Get current user profile
export function fetchUserProfile() {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  return getJson<User>('/accounts/me/', undefined, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

// PUT /accounts/me/ - Update user profile
export function updateUserProfile(data: Partial<User>) {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  return putJson<User>('/accounts/me/', data, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

// PATCH /accounts/me/ - Partially update user profile
export function patchUserProfile(data: Partial<User>) {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  return patchJson<User>('/accounts/me/', data, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

// Habbo validation interfaces
export interface HabboVerifyRequest {
  nick_habbo: string;
}

export interface HabboVerifyResponse {
  message: string;
  palavra_validacao: string;
  nick_habbo: string;
  validation_id: number;
  eta_time: string;
  current_time: string;
}

export interface HabboValidationStatus {
  id: number;
  nick_habbo: string;
  palavra_validacao: string;
  status: string;
  resultado?: string;
  created_at: string;
  updated_at: string;
}

export interface HabboUnlinkResponse {
  message: string;
  nick_anterior: string;
}

// POST /accounts/habbo/verify/ - Iniciar validação do nick do Habbo
export function verifyHabboNick(data: HabboVerifyRequest) {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  return postJson<HabboVerifyResponse>('/accounts/habbo/verify/', data, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

// GET /accounts/habbo/status/ - Verificar status da validação do Habbo
export function getHabboValidationStatus(validationId?: number) {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  const params = validationId ? { validation_id: validationId } : undefined;
  return getJson<HabboValidationStatus>('/accounts/habbo/status/', params, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

// POST /accounts/habbo/unlink/ - Desvincular nick do Habbo
export function unlinkHabboNick() {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  return postJson<HabboUnlinkResponse>('/accounts/habbo/unlink/', {}, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

// POST /accounts/habbo/confirm/ - Confirmar validação do Habbo manualmente
export function confirmHabboValidation() {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  return postJson<{ message: string }>('/accounts/habbo/confirm/', {}, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

// POST /token/refresh/ - Refresh access token
export interface TokenRefreshResponse {
  access: string;
}

export function refreshAccessToken(): Promise<TokenRefreshResponse> {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) {
    throw new Error('Refresh token não encontrado');
  }
  return postJson<TokenRefreshResponse>('/token/refresh/', {
    refresh: refreshToken,
  });
}

