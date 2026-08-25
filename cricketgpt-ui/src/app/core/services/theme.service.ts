import { Injectable, signal } from '@angular/core';

export type Theme = 'light' | 'dark';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly STORAGE_KEY = 'cgpt-theme';

  readonly theme = signal<Theme>(this.loadTheme());

  toggle(): void {
    const next: Theme = this.theme() === 'dark' ? 'light' : 'dark';
    this.apply(next);
  }

  private apply(t: Theme): void {
    this.theme.set(t);
    document.documentElement.setAttribute('data-theme', t);
    localStorage.setItem(this.STORAGE_KEY, t);
  }

  private loadTheme(): Theme {
    const stored = localStorage.getItem(this.STORAGE_KEY) as Theme | null;
    const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const theme = stored ?? preferred;
    document.documentElement.setAttribute('data-theme', theme);
    return theme;
  }
}
