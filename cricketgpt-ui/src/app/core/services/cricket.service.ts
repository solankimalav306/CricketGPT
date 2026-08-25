import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CricketResponse, QueryRequest } from '../models/cricket.models';

@Injectable({ providedIn: 'root' })
export class CricketService {
  private readonly baseUrl = '/api';

  constructor(private http: HttpClient) {}

  query(payload: QueryRequest): Observable<CricketResponse> {
    return this.http.post<CricketResponse>(`${this.baseUrl}/query`, payload);
  }

  health(): Observable<{ status: string }> {
    return this.http.get<{ status: string }>(`${this.baseUrl}/health`);
  }
}
