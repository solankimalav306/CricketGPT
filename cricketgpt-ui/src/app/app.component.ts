import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ThemeService } from './core/services/theme.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `<router-outlet />`,
  styles: [],
})
export class AppComponent {
  // ThemeService is still needed by home component, keep it injectable
  private readonly _theme = inject(ThemeService);
}
