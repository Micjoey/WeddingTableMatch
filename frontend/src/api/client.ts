import axios, { AxiosInstance } from 'axios';
import {
  SolveRequest,
  SolveResponse,
  ScoreRequest,
  TableScore,
  SwapRequest,
  SwapSuggestion,
} from '../types';

const API_BASE_URL = '/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // Run the solver to generate seating assignments
  async solve(request: SolveRequest): Promise<SolveResponse> {
    const response = await this.client.post<SolveResponse>('/solve', request);
    return response.data;
  }

  // Score existing assignments without re-solving
  async score(request: ScoreRequest): Promise<TableScore[]> {
    const response = await this.client.post<TableScore[]>('/score', request);
    return response.data;
  }

  // Get swap suggestions for a specific guest
  async suggestSwap(request: SwapRequest): Promise<SwapSuggestion[]> {
    const response = await this.client.post<{ suggestions: SwapSuggestion[] }>(
      '/suggest-swap',
      request
    );
    return response.data.suggestions;
  }

  // Health check
  async health(): Promise<{ status: string }> {
    const response = await this.client.get<{ status: string }>('/health');
    return response.data;
  }
}

export const apiClient = new ApiClient();
