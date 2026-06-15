// sdlc-os/colony/cost-enforcer.test.ts
import { describe, it, expect } from 'vitest';
import { CostEnforcer } from './cost-enforcer.ts';

describe('CostEnforcer', () => {
  it('allows dispatch when under budget', () => {
    const enforcer = new CostEnforcer(50.0);
    enforcer.recordCost('ws-001', 10.0);
    const check = enforcer.checkBudget('ws-001');
    expect(check.allowed).toBe(true);
    expect(check.phase).toBe('normal');
  });

  it('warns at 80% budget — disables discovery', () => {
    const enforcer = new CostEnforcer(50.0);
    enforcer.recordCost('ws-001', 42.0);
    const check = enforcer.checkBudget('ws-001');
    expect(check.allowed).toBe(true);
    expect(check.phase).toBe('warning');
    expect(check.discovery_disabled).toBe(true);
  });

  it('blocks new dispatches at 100% budget', () => {
    const enforcer = new CostEnforcer(50.0);
    enforcer.recordCost('ws-001', 52.0);
    const check = enforcer.checkBudget('ws-001');
    expect(check.allowed).toBe(false);
    expect(check.phase).toBe('exceeded');
  });

  it('tracks cost per workstream independently', () => {
    const enforcer = new CostEnforcer(50.0);
    enforcer.recordCost('ws-001', 48.0);
    enforcer.recordCost('ws-002', 5.0);
    expect(enforcer.checkBudget('ws-001').phase).toBe('warning');
    expect(enforcer.checkBudget('ws-002').phase).toBe('normal');
  });

  it('fails closed: refuses a zero ceiling (no NaN-ratio fail-open)', () => {
    expect(() => new CostEnforcer(0)).toThrow(/positive finite ceiling/);
  });

  it('fails closed: refuses a negative ceiling', () => {
    expect(() => new CostEnforcer(-5)).toThrow(/positive finite ceiling/);
  });

  it('fails closed: refuses a NaN ceiling', () => {
    expect(() => new CostEnforcer(Number.NaN)).toThrow(/positive finite ceiling/);
  });
});
