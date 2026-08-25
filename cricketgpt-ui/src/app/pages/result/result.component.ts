import { Component, OnInit, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { CricketResponse } from '../../core/models/cricket.models';
import { ThinkingPanelComponent } from '../../components/thinking-panel/thinking-panel.component';
import { PredictionCardComponent } from '../../components/prediction-card/prediction-card.component';
import { WinProbabilityChartComponent } from '../../components/win-probability-chart/win-probability-chart.component';
import { WhySectionComponent } from '../../components/why-section/why-section.component';
import { VerdictCardComponent } from '../../components/verdict-card/verdict-card.component';

import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Component({
  selector: 'app-result',
  standalone: true,
  imports: [
    RouterLink,
    ThinkingPanelComponent,
    PredictionCardComponent,
    WinProbabilityChartComponent,
    WhySectionComponent,
    VerdictCardComponent,
  ],
  templateUrl: './result.component.html',
  styleUrl: './result.component.scss',
})
export class ResultComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly sanitizer = inject(DomSanitizer);

  data = signal<CricketResponse | null>(null);
  activeTab = signal<'answer' | 'raw'>('answer');
  copied = signal(false);
  sanitizedHtml = signal<SafeHtml | null>(null);

  ngOnInit(): void {
    const nav = this.router.getCurrentNavigation();
    const state = nav?.extras?.state as { data?: CricketResponse } | undefined;
    const res = state?.['data'] ?? history.state?.['data'];
    if (res) {
      this.data.set(res);
      if (res.html) {
        this.sanitizedHtml.set(this.sanitizer.bypassSecurityTrustHtml(res.html));
      }
    }
  }

  setTab(tab: 'answer' | 'raw'): void {
    this.activeTab.set(tab);
  }

  copyRaw(): void {
    const raw = this.data()?.answer?.raw ?? '';
    navigator.clipboard.writeText(raw).then(() => {
      this.copied.set(true);
      setTimeout(() => this.copied.set(false), 2000);
    });
  }

  hasWinProb(): boolean {
    const wp = this.data()?.answer?.win_probability;
    return !!(wp && (wp.team_a || wp.team_b || wp.draw));
  }
}
