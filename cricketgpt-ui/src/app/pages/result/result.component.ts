import { Component, OnInit, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { CricketResponse } from '../../core/models/cricket.models';
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

  hasWinProb(): boolean {
    const wp = this.data()?.answer?.win_probability;
    return !!(wp && (wp.team_a || wp.team_b || wp.draw));
  }
}
