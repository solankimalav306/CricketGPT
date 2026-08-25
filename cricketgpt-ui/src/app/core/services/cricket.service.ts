import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CricketResponse, PlannerProgress, QueryRequest } from '../models/cricket.models';

@Injectable({ providedIn: 'root' })
export class CricketService {
  private readonly baseUrl = '/api';

  constructor(private http: HttpClient) {}

  query(payload: QueryRequest): Observable<CricketResponse> {
    return this.http.post<CricketResponse>(`${this.baseUrl}/query`, payload);
  }

  startQuery(payload: QueryRequest): Observable<{ job_id: string }> {
    return this.http.post<{ job_id: string }>(`${this.baseUrl}/query/start`, payload);
  }

  watchQuery(jobId: string, handlers: { step: (data: { id: string; label: string; status: string }) => void; planner: (data: PlannerProgress) => void; complete: (data: { result: CricketResponse }) => void; error: (data: { detail: string }) => void }): EventSource {
    const source = new EventSource(`${this.baseUrl}/query/${jobId}/events`);
    source.addEventListener('step', event => handlers.step(JSON.parse((event as MessageEvent).data)));
    source.addEventListener('planner', event => handlers.planner(JSON.parse((event as MessageEvent).data)));
    source.addEventListener('complete', event => handlers.complete(JSON.parse((event as MessageEvent).data)));
    source.addEventListener('error', event => handlers.error(JSON.parse((event as MessageEvent).data)));
    return source;
  }

  health(): Observable<{ status: string }> {
    return this.http.get<{ status: string }>(`${this.baseUrl}/health`);
  }
}
