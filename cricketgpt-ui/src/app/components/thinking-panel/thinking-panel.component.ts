import { Component, Input, OnChanges, signal } from '@angular/core';
import { NgClass, TitleCasePipe } from '@angular/common';
import { PipelineStep } from '../../core/models/cricket.models';

@Component({
  selector: 'app-thinking-panel',
  standalone: true,
  imports: [NgClass, TitleCasePipe],
  templateUrl: './thinking-panel.component.html',
  styleUrl: './thinking-panel.component.scss',
})
export class ThinkingPanelComponent implements OnChanges {
  @Input() steps: PipelineStep[] = [];

  expandedStep = signal<string | null>(null);

  ngOnChanges(): void {
    // Auto-expand last step on load
    if (this.steps.length > 0) {
      this.expandedStep.set(this.steps[this.steps.length - 1].id);
    }
  }

  toggle(id: string): void {
    this.expandedStep.set(this.expandedStep() === id ? null : id);
  }

  isExpanded(id: string): boolean {
    return this.expandedStep() === id;
  }

  detailKeys(detail: Record<string, unknown>): string[] {
    return Object.keys(detail).filter(k => detail[k] !== null && detail[k] !== undefined);
  }

  formatValue(val: unknown): string {
    if (Array.isArray(val)) {
      if (val.length === 0) return '—';
      return JSON.stringify(val, null, 2);
    }
    if (typeof val === 'object' && val !== null) return JSON.stringify(val, null, 2);
    return String(val ?? '—');
  }

  isArray(val: unknown): boolean {
    return Array.isArray(val);
  }

  asArray(val: unknown): unknown[] {
    return Array.isArray(val) ? val : [];
  }

  isPlanArray(key: string, val: unknown): boolean {
    return key === 'plan' && Array.isArray(val);
  }

  planSteps(val: unknown): Array<{agent: string; task: string}> {
    if (!Array.isArray(val)) return [];
    return val as Array<{agent: string; task: string}>;
  }
}
