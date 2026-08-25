import { Component, Input, AfterViewInit, ElementRef, ViewChild, OnChanges } from '@angular/core';
import { WinProbability } from '../../core/models/cricket.models';

@Component({
  selector: 'app-win-probability-chart',
  standalone: true,
  template: `
    <div class="chart-card card">
      <div class="chart-header">
        <span class="chart-icon">📊</span>
        <div>
          <div class="chart-title">Win Probability</div>
          <div class="chart-subtitle">Based on historical data & current form</div>
        </div>
      </div>

      <!-- Bar chart rows -->
      <div class="bars">
        @if (prob.team_a) {
          <div class="bar-row">
            <div class="bar-label">
              <span class="team-flag">🏏</span>
              <span>{{ prob.team_a.name }}</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill bar-a" [style.width.%]="prob.team_a.value" [style.animation-delay]="'0.1s'">
                <span class="bar-value">{{ prob.team_a.value }}%</span>
              </div>
            </div>
          </div>
        }
        @if (prob.team_b) {
          <div class="bar-row">
            <div class="bar-label">
              <span class="team-flag">🏏</span>
              <span>{{ prob.team_b.name }}</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill bar-b" [style.width.%]="prob.team_b.value" [style.animation-delay]="'0.2s'">
                <span class="bar-value">{{ prob.team_b.value }}%</span>
              </div>
            </div>
          </div>
        }
        @if (prob.draw) {
          <div class="bar-row">
            <div class="bar-label">
              <span class="team-flag">🤝</span>
              <span>Draw</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill bar-draw" [style.width.%]="prob.draw.value" [style.animation-delay]="'0.3s'">
                <span class="bar-value">{{ prob.draw.value }}%</span>
              </div>
            </div>
          </div>
        }
      </div>

      <!-- Doughnut canvas -->
      <div class="donut-wrap">
        <canvas #donutCanvas width="160" height="160"></canvas>
        <div class="donut-center">
          <div class="donut-label">Total</div>
          <div class="donut-value">100%</div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .chart-card {
      padding: 24px;
    }

    .chart-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 24px;

      .chart-icon { font-size: 24px; }
      .chart-title { font-size: 15px; font-weight: 700; color: var(--text-primary); }
      .chart-subtitle { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
    }

    .bars {
      display: flex;
      flex-direction: column;
      gap: 14px;
      margin-bottom: 24px;
    }

    .bar-row {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .bar-label {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      font-weight: 600;
      color: var(--text-primary);
      .team-flag { font-size: 16px; }
    }

    .bar-track {
      height: 32px;
      background: var(--bg-sidebar);
      border-radius: 8px;
      overflow: hidden;
      position: relative;
    }

    .bar-fill {
      height: 100%;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: flex-end;
      padding-right: 10px;
      min-width: 40px;
      width: 0;
      animation: growBar 1s ease forwards;
      position: relative;
    }

    @keyframes growBar {
      from { width: 0 !important; }
    }

    .bar-a { background: linear-gradient(90deg, var(--accent), #60a5fa); }
    .bar-b { background: linear-gradient(90deg, var(--green), #4ade80); }
    .bar-draw { background: linear-gradient(90deg, var(--amber), #fbbf24); }

    .bar-value {
      font-size: 12px;
      font-weight: 700;
      color: white;
      white-space: nowrap;
    }

    .donut-wrap {
      display: flex;
      justify-content: center;
      position: relative;
      width: 160px;
      margin: 0 auto;

      canvas { display: block; }
    }

    .donut-center {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      text-align: center;
      pointer-events: none;

      .donut-label { font-size: 11px; color: var(--text-muted); font-weight: 500; }
      .donut-value { font-size: 18px; font-weight: 800; color: var(--text-primary); }
    }
  `],
})
export class WinProbabilityChartComponent implements AfterViewInit, OnChanges {
  @Input() prob: WinProbability = {};
  @ViewChild('donutCanvas') canvasRef!: ElementRef<HTMLCanvasElement>;

  ngAfterViewInit(): void {
    this.drawDonut();
  }

  ngOnChanges(): void {
    if (this.canvasRef) this.drawDonut();
  }

  private drawDonut(): void {
    const canvas = this.canvasRef?.nativeElement;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const data = [
      { value: this.prob.team_a?.value ?? 0, color: '#3b82f6' },
      { value: this.prob.team_b?.value ?? 0, color: '#4ade80' },
      { value: this.prob.draw?.value ?? 0,   color: '#fbbf24' },
    ].filter(d => d.value > 0);

    const total = data.reduce((s, d) => s + d.value, 0) || 100;
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const outerR = 70;
    const innerR = 48;
    let angle = -Math.PI / 2;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    data.forEach(({ value, color }) => {
      const slice = (value / total) * 2 * Math.PI;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, outerR, angle, angle + slice);
      ctx.closePath();
      ctx.fillStyle = color;
      ctx.fill();
      angle += slice;
    });

    // Inner hole
    ctx.beginPath();
    ctx.arc(cx, cy, innerR, 0, 2 * Math.PI);
    // Use a background-matching fill — white for light, dark for dark
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    ctx.fillStyle = isDark ? '#111827' : '#ffffff';
    ctx.fill();
  }
}
