import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CricketService } from '../../core/services/cricket.service';
import { CricketResponse, PlannerProgress } from '../../core/models/cricket.models';
import { ThemeService } from '../../core/services/theme.service';

const EXAMPLE_QUERIES = [
  'How will Jadeja perform against left-handed batsmen in the upcoming Sri Lanka Tests?',
  'Analyze India\'s probability in Melbourne considering historical day-night venue stats.',
  'Analyze Bumrah\'s efficiency against tail-enders under overcast conditions in London.',
  'Evaluate Kohli\'s recent performance metrics against leg spin in the subcontinent.'
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
  readonly themeService = inject(ThemeService);

  query = signal('');
  loading = signal(false);
  error = signal('');
  planner = signal<PlannerProgress | null>(null);
  activeStep = signal('Preparing analysis');
  runningAgent = signal('');
  completedAgents = signal<string[]>([]);
  exampleQueries = EXAMPLE_QUERIES;

  setExample(q: string): void {
    this.query.set(q);
  }

  submit(): void {
    if (!this.query().trim() || this.loading()) return;
    this.loading.set(true);
    this.error.set('');
    this.planner.set(null);
    this.runningAgent.set('');
    this.completedAgents.set([]);
    this.activeStep.set('Starting the analysis team');
    this.cricketService.startQuery({ query: this.query() }).subscribe({
      next: ({ job_id }) => {
        const stream = this.cricketService.watchQuery(job_id, {
          step: step => {
            this.activeStep.set(`${step.label} ${step.status === 'completed' ? 'completed' : 'is working'}`);
            if (step.status === 'completed') this.completedAgents.update(done => [...new Set([...done, step.id])]);
            else this.runningAgent.set(step.id);
          },
          planner: plan => this.planner.set(plan),
          complete: ({ result }) => { stream.close(); this.loading.set(false); this.router.navigateByUrl('/result', { state: { data: result } }); },
          error: ({ detail }) => { stream.close(); this.loading.set(false); this.error.set(detail); },
        });
      },
      error: err => { this.loading.set(false); this.error.set(err?.error?.detail ?? 'Unable to start the analysis.'); },
    });
  }

  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      this.submit();
    }
  }

  taskId(task: { agent?: string }): string { return task.agent?.replace('final_reasoning', 'final_reasoning_agent') ?? ''; }
  taskText(task: { task?: string; agent?: string; description?: string }): string { return task.task || task.description || task.agent || 'Specialist task'; }
}
