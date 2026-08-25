import { Component, Input } from '@angular/core';
import { WhyBullet } from '../../core/models/cricket.models';

const ICON_MAP: Record<string, string> = {
  batting:     '🏏',
  bowling:     '⚾',
  venue:       '🏟️',
  weather:     '🌤️',
  'head-to-head': '⚔️',
  historical:  '📜',
  default:     '📌',
};

@Component({
  selector: 'app-why-section',
  standalone: true,
  template: `
    <div class="why-card card">
      <div class="why-header">
        <span class="why-icon">🔍</span>
        <div>
          <div class="why-title">Why?</div>
          <div class="why-subtitle">Evidence & Reasoning</div>
        </div>
      </div>

      @if (bullets.length > 0) {
        <div class="bullets">
          @for (bullet of bullets; track bullet.label; let i = $index) {
            <div class="bullet-item" [style.animation-delay]="(i * 0.1) + 's'">
              <div class="bullet-icon">{{ getIcon(bullet.label) }}</div>
              <div class="bullet-content">
                <div class="bullet-label">{{ bullet.label }}</div>
                <div class="bullet-text">{{ bullet.text }}</div>
              </div>
            </div>
          }
        </div>
      } @else if (rawText) {
        <div class="raw-why markdown-content" [innerHTML]="rawText"></div>
      }
    </div>
  `,
  styles: [`
    .why-card { padding: 24px; }

    .why-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 20px;

      .why-icon { font-size: 24px; }
      .why-title { font-size: 15px; font-weight: 700; color: var(--text-primary); }
      .why-subtitle { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
    }

    .bullets {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .bullet-item {
      display: flex;
      gap: 14px;
      padding: 14px;
      background: var(--bg-sidebar);
      border-radius: var(--radius-md);
      border: 1px solid var(--border);
      opacity: 0;
      animation: fadeInUp 0.5s ease forwards;
      transition: background 0.2s ease, transform 0.2s ease;

      &:hover {
        background: var(--bg-card-hover);
        transform: translateX(4px);
      }
    }

    .bullet-icon {
      font-size: 22px;
      flex-shrink: 0;
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--bg-card);
      border-radius: var(--radius-sm);
      border: 1px solid var(--border);
    }

    .bullet-content {
      flex: 1;
      min-width: 0;
    }

    .bullet-label {
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--accent);
      margin-bottom: 4px;
    }

    .bullet-text {
      font-size: 13.5px;
      color: var(--text-secondary);
      line-height: 1.6;
    }

    .raw-why {
      font-size: 14px;
      line-height: 1.7;
    }
  `],
})
export class WhySectionComponent {
  @Input() bullets: WhyBullet[] = [];
  @Input() rawText = '';

  getIcon(label: string): string {
    const lower = label.toLowerCase();
    for (const [key, icon] of Object.entries(ICON_MAP)) {
      if (lower.includes(key)) return icon;
    }
    return ICON_MAP['default'];
  }
}
