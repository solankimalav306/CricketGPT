import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-verdict-card',
  standalone: true,
  template: `
    <div class="verdict-card card">
      <div class="verdict-header">
        <div class="verdict-badge">
          <span>⚖️</span>
          <span>Verdict</span>
        </div>
        <div class="verdict-gavel">Final Judgement</div>
      </div>
      <div class="verdict-divider"></div>
      <p class="verdict-text">{{ text }}</p>
      <div class="verdict-footer">
        <span class="verdict-tag">AI Analysis</span>
        <span class="verdict-tag">Historical Data</span>
        <span class="verdict-tag">Live Stats</span>
      </div>
    </div>
  `,
  styles: [`
    .verdict-card {
      padding: 24px;
      border: 1px solid var(--border);
      position: relative;
      overflow: hidden;

      &::before {
        content: '⚖️';
        position: absolute;
        right: -10px;
        top: -10px;
        font-size: 80px;
        opacity: 0.04;
        transform: rotate(15deg);
        pointer-events: none;
      }
    }

    .verdict-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
    }

    .verdict-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 15px;
      font-weight: 700;
      color: var(--text-primary);

      span:first-child { font-size: 22px; }
    }

    .verdict-gavel {
      font-size: 11px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      background: var(--bg-sidebar);
      padding: 4px 10px;
      border-radius: 99px;
    }

    .verdict-divider {
      height: 2px;
      background: linear-gradient(90deg, var(--accent), var(--purple), transparent);
      border-radius: 2px;
      margin-bottom: 16px;
    }

    .verdict-text {
      font-size: 14px;
      line-height: 1.75;
      color: var(--text-secondary);
    }

    .verdict-footer {
      display: flex;
      gap: 8px;
      margin-top: 16px;
      flex-wrap: wrap;
    }

    .verdict-tag {
      font-size: 11px;
      font-weight: 600;
      color: var(--accent);
      background: var(--accent-light);
      border-radius: 99px;
      padding: 3px 10px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
  `],
})
export class VerdictCardComponent {
  @Input() text = '';
}
