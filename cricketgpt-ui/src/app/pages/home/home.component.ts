import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CricketService } from '../../core/services/cricket.service';
import { CricketResponse } from '../../core/models/cricket.models';

const EXAMPLE_QUERIES = [
  'Who is the toughest batsman Ravindra Jadeja will face in the upcoming Sri Lanka series?',
  'What are India\'s chances of winning the next Test against Australia?',
  'Analyze Jasprit Bumrah\'s performance against left-handed batsmen in England.',
  'Predict the win probability for India vs Pakistan in the upcoming T20 World Cup.',
];

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
})
export class HomeComponent {
  private readonly cricketService = inject(CricketService);
  private readonly router = inject(Router);

  query = signal('');
  loading = signal(false);
  error = signal('');
  exampleQueries = EXAMPLE_QUERIES;

  setExample(q: string): void {
    this.query.set(q);
  }

  submit(): void {
    if (!this.query().trim() || this.loading()) return;
    this.loading.set(true);
    this.error.set('');

    this.cricketService.query({ query: this.query() }).subscribe({
      next: (res: CricketResponse) => {
        this.loading.set(false);
        // Store in state service / navigate with state
        this.router.navigateByUrl('/result', { state: { data: res } });
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err?.error?.detail ?? 'Something went wrong. Is the backend running?');
      },
    });
  }

  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      this.submit();
    }
  }
}
