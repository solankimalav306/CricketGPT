import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-prediction-card',
  standalone: true,
  template: `
    <div class="prediction-card">
      <div class="prediction-header">
        <span class="prediction-icon">🏆</span>
        <div>
          <div class="prediction-label">AI Prediction</div>
          <div class="prediction-sublabel">Key Insight</div>
        </div>
      </div>
      <p class="prediction-text">{{ text }}</p>
    </div>
  `,
  styles: [`
    .prediction-card {
      background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
      border-radius: var(--radius-lg);
      padding: 24px;
      color: white;
    }

    .prediction-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }

    .prediction-icon {
      font-size: 28px;
      filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
    }

    .prediction-label {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      opacity: 0.8;
    }

    .prediction-sublabel {
      font-size: 16px;
      font-weight: 700;
      letter-spacing: -0.02em;
    }

    .prediction-text {
      font-size: 15px;
      line-height: 1.7;
      opacity: 0.95;
      font-weight: 400;
    }
  `],
})
export class PredictionCardComponent {
  @Input() text = '';
}
