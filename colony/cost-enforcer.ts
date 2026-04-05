// sdlc-os/colony/cost-enforcer.ts

export interface BudgetCheck {
  allowed: boolean;
  phase: 'normal' | 'warning' | 'exceeded';
  discovery_disabled: boolean;
  spent_usd: number;
  ceiling_usd: number;
  reason?: string;
}

export class CostEnforcer {
  private ceiling: number;
  private costs: Map<string, number> = new Map();

  constructor(ceilingUsd: number) {
    this.ceiling = ceilingUsd;
  }

  recordCost(workstream_id: string, cost_usd: number): void {
    const current = this.costs.get(workstream_id) ?? 0;
    this.costs.set(workstream_id, current + cost_usd);
  }

  checkBudget(workstream_id: string): BudgetCheck {
    const spent = this.costs.get(workstream_id) ?? 0;
    const ratio = spent / this.ceiling;

    if (ratio >= 1.0) {
      return {
        allowed: false,
        phase: 'exceeded',
        discovery_disabled: true,
        spent_usd: spent,
        ceiling_usd: this.ceiling,
        reason: `Budget exceeded: $${spent.toFixed(2)} / $${this.ceiling.toFixed(2)}`,
      };
    }

    if (ratio >= 0.8) {
      return {
        allowed: true,
        phase: 'warning',
        discovery_disabled: true,
        spent_usd: spent,
        ceiling_usd: this.ceiling,
        reason: `Budget warning (${(ratio * 100).toFixed(0)}%): discovery beads disabled`,
      };
    }

    return {
      allowed: true,
      phase: 'normal',
      discovery_disabled: false,
      spent_usd: spent,
      ceiling_usd: this.ceiling,
    };
  }

  getSpent(workstream_id: string): number {
    return this.costs.get(workstream_id) ?? 0;
  }
}
