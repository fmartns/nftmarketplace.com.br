import { getJson, postJson } from './client';

export interface OrderItem {
  id: number;
  item_type: 'legacy' | 'nft';
  item_name: string;
  item_image_url?: string;
  quantity: number;
  unit_price: string;
  total_price: string;
  created_at: string;
}

export interface Order {
  id: number;
  order_id: string;
  status: 'pending' | 'paid' | 'processing' | 'delivered' | 'cancelled' | 'refunded';
  subtotal: string;
  discount_amount: string;
  total: string;
  coupon?: string;
  paid_at?: string;
  delivered: boolean;
  delivered_at?: string;
  notes?: string;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
}

// GET /orders/ - Get user orders
export async function fetchUserOrders(): Promise<Order[]> {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  const response = await getJson<Order[] | { results: Order[] }>('/orders/', undefined, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  
  // Handle paginated response (DRF returns { results: [...] })
  if (Array.isArray(response)) {
    return response;
  }
  if (response && typeof response === 'object' && 'results' in response) {
    return response.results;
  }
  return [];
}

export interface CreateOrderRequest {
  items: Array<{
    item_type: 'legacy' | 'nft';
    item_id: number;
    quantity?: number;
  }>;
  coupon_code?: string;
  notes?: string;
}

// POST /orders/ - Create new order
export async function createOrder(data: CreateOrderRequest): Promise<Order> {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  return postJson<Order>('/orders/', data, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

// GET /orders/{order_id}/ - Get order by ID
export async function fetchOrderById(orderId: string): Promise<Order> {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  if (!token) {
    throw new Error('Token não encontrado. Faça login novamente.');
  }
  
  // Encode o order_id para URL (o # precisa ser %23)
  const encodedOrderId = encodeURIComponent(orderId);
  console.log('fetchOrderById - orderId original:', orderId);
  console.log('fetchOrderById - orderId codificado:', encodedOrderId);
  console.log('fetchOrderById - URL completa:', `/orders/${encodedOrderId}/`);
  
  try {
    const order = await getJson<Order>(`/orders/${encodedOrderId}/`, undefined, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    console.log('fetchOrderById - Resposta recebida:', order);
    console.log('fetchOrderById - Tipo da resposta:', typeof order);
    console.log('fetchOrderById - order_id na resposta:', order?.order_id);
    
    if (!order || !order.order_id) {
      throw new Error('Resposta inválida do servidor: pedido não contém order_id');
    }
    
    return order;
  } catch (error: any) {
    console.error('fetchOrderById - Erro na requisição:', error);
    throw error;
  }
}

