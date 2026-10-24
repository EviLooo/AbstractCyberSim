import type { ActorView, DecisionTrace, EpisodeConfig, Frame, Host, Message, Run } from '../../src/types';

// Synthetic UI test data only: no native episode, provider call, or research result.
export const TEST_RUN_ID = 'a'.repeat(32);
export const OWN_HOST = 'TEST_OWN_HOST';
export const OBSERVED_HOST = 'TEST_OBSERVED_HOST';
export const PEER_HOST = 'TEST_PEER_ONLY_HOST';
export const PEER_ZONE = 'TEST_PEER_ONLY_ZONE';
export const OWN_EVIDENCE = 'TEST_WORKER_0_EVIDENCE';
export const PEER_EVIDENCE = 'TEST_WORKER_1_PRIVATE_EVIDENCE';
export const PEER_REPORT = 'TEST_WORKER_1_COORDINATOR_REPORT';
export const TRUTH_ONLY = 'TEST_PRIVILEGED_STRUCTURE';

const config = {
  schema_version: '2.0', name: 'TEST/MOCK mounted UI', purpose: 'evaluation',
  scenario: {
    profile: 'enterprise_cc4_research', world_seed: 101, targets: [OBSERVED_HOST], defender: 'passive',
    cc4: { user_hosts: 3, server_hosts: 1, addon_services: 0, response_delay: 2, response_cooldown: 10, response_budget: 0 },
    complexity: null, mission: { hold_ticks: 1, deadline_tick: null, objectives: [] },
    research: {
      module_version: '1.0', recipe: 'investigate', conditions: 'paired', condition_variant: 'import_enabled',
      credential_variant: 'valid', capability_coupling: 'separate', initial_access: 'common_entry',
      evidence: { observation_delay: 0, stale_after: 8 },
      change: { mode: 'none', response_delay: 4, response_budget: 0 },
      seed_namespaces: { recipe: 401, event: 701 }, catalog: 'minimal_access_v1',
      background_access: 'deny', native_mission_phase_policy: 'fixed_research_policy_v1',
    },
  },
  team: { architecture: 'hierarchy', workers: 2, claim_ttl: 5 },
  communication: {
    extra_delay: 0, loss_probability: 0, bytes_per_tick: 1000000, envelopes_per_tick: 64,
    ttl: 10, seed: 17, verified_intel: true, links: null, interruptions: [],
  },
  cognition: {
    provider: 'scripted', scripted_policy: 'evidence_controller',
    search: { risk_weight: 8, failure_penalty: 6, unknown_edge_penalty: 4, max_expansions: 128 },
    action_retry_limit: 2, failure_backoff_ticks: 0, model: '', temperature: 0,
    max_output_tokens: 512, max_context_bytes: 128000, max_team_tokens: 40000, timeout_seconds: 60,
  },
  schedule: { mode: 'per_worker', seed: 27, max_ticks: 180 },
  resources: { team_access_attempts: 12 },
} satisfies EpisodeConfig;

const run = {
  id: TEST_RUN_ID, name: config.name, profile: config.scenario.profile, architecture: 'hierarchy',
  workers: 2, reasoners: 3, status: 'stopped', tick: 4, purpose: 'evaluation', manual_intervention: false,
  world_id: 'TEST_MOCK_WORLD_NOT_RESEARCH', created_at: '2026-01-01T00:00:00Z',
} satisfies Run;

function message(id: string, sender: string, recipient: string, text: string, status = 'delivered'): Message {
  return {
    id, sender, recipient, kind: 'report', status, created_tick: 1, due_tick: 2,
    ...(status === 'delivered' ? { resolved_tick: 2 } : {}),
    bytes: 32, evidence_ids: [], payload: { text },
  };
}

const ownDelivered = message('test-own-delivered', 'Coordinator', 'Red_0', 'TEST_DELIVERED_TO_WORKER_0');
const pending = message('test-pending', 'Coordinator', 'Red_0', 'TEST_NOT_DELIVERED_YET', 'queued');
const peerReports = [1, 2, 3].map(i => message(`test-peer-${i}`, 'Red_1', 'Coordinator', PEER_REPORT));

function host(id: string, subnet: string, ip: string, sessions: Host['sessions'], target = false): Host {
  return { id, subnet, router: false, target, interfaces: [{ 'IP Address': ip }], system: {}, services: {}, sessions };
}

function worker(actor: string, hostname: string, ip: string, privileged: boolean, text: string): ActorView {
  return {
    actor, mission: { target_names: [OBSERVED_HOST], requirements: { hold_ticks: 1 } },
    native: {
      known: { hostname: [hostname], ip_address: [ip], subnet: [privileged ? '10.1.0.0/24' : '10.0.0.0/24'] },
      sessions: [{ id: 0, hostname, active: true, controller: true, privileged }],
      scan_cache: {}, pending_action: null, pivot_enabled: false, catalog: {}, possessed_tokens: [],
      access_resources: { limit: 12, reserved: 0, remaining: 12, settled: 0 },
    },
    hosts: {}, reported_hosts: {}, inbox: actor === 'Red_0' ? [ownDelivered] : [], history: [],
    research_evidence: [{
      host: ip, kind: 'note', evidence_id: `test-note-${actor}`, origin: actor, source: 'self_observed',
      observed_tick: 1, received_tick: 1, age: 3, stale: false, text,
    }],
  };
}

function decision(actor: string, target: string): DecisionTrace {
  return {
    policy: 'evidence_controller', version: 'TEST', actor, tick: 4, status: 'waiting',
    organization: 'hierarchy', candidate_count: 0, own_missing_goals: [],
    selected: { action: 'Sleep', session: 0, target }, state_change: {}, alternatives: [],
  };
}

const ownWorker = worker('Red_0', OWN_HOST, '10.0.0.1', false, OWN_EVIDENCE);
ownWorker.native.known.hostname.push(OBSERVED_HOST);
ownWorker.native.known.ip_address.push('10.0.0.2');
ownWorker.research_evidence!.push({
  host: '10.0.0.2', source_host: OWN_HOST, kind: 'diagnostic', probe: 'connectivity', port: 80,
  response: 'tcp_handshake', evidence_id: 'test-own-probe', origin: 'Red_0', source: 'self_observed',
  observed_tick: 3, received_tick: 3, age: 1, stale: false,
});

const peerWorker = worker('Red_1', PEER_HOST, '10.1.0.9', true, PEER_EVIDENCE);
peerWorker.native.sessions.push({ id: 1, hostname: OBSERVED_HOST, active: true, controller: true, privileged: true });

const frame = {
  tick: 4, status: 'stopped', engine_profile: config.scenario.profile,
  truth: {
    subnets: [{ id: 'TEST_SHARED_ZONE', cidr: '10.0.0.0/24' }, { id: PEER_ZONE, cidr: '10.1.0.0/24' }],
    hosts: [
      host(OWN_HOST, 'TEST_SHARED_ZONE', '10.0.0.1', [{ id: 0, agent: 'Red_0', username: 'user', privileged: false }]),
      host(OBSERVED_HOST, 'TEST_SHARED_ZONE', '10.0.0.2', [{ id: 1, agent: 'Red_1', username: 'root', privileged: true }], true),
      host(PEER_HOST, PEER_ZONE, '10.1.0.9', [{ id: 0, agent: 'Red_1', username: 'root', privileged: true }]),
    ],
    edges: [
      { id: 'test-physical-observed', source: OWN_HOST, target: OBSERVED_HOST },
      { id: 'test-physical-hidden', source: OBSERVED_HOST, target: PEER_HOST },
    ],
  },
  private_views: { Red_0: ownWorker, Red_1: peerWorker },
  messages: [ownDelivered, pending, ...peerReports], actions: [], observations: {},
  score: { controlled_hosts: [OWN_HOST, OBSERVED_HOST, PEER_HOST], privileged_hosts: [OBSERVED_HOST, PEER_HOST], target_count: 1, targets_reached: 1, mission_success: false },
  cognition: { is_llm: false, calls: 0, charged_tokens: 0, provider: 'scripted' },
  coordinator: { delivered_reports: Object.fromEntries(peerReports.map(m => [m.id, m])), assignments: {} },
  communication_topology: [
    { sender: 'Coordinator', recipient: 'Red_0', active: true, interruption_indices: [] },
    { sender: 'Red_0', recipient: 'Coordinator', active: true, interruption_indices: [] },
    { sender: 'Coordinator', recipient: 'Red_1', active: false, interruption_indices: [0] },
    { sender: 'Red_1', recipient: 'Coordinator', active: true, interruption_indices: [] },
  ],
  diagnostics: { structure: { fixture: TRUTH_ONLY }, behavior: {} },
  decisions: { Red_0: decision('Red_0', OWN_HOST), Red_1: decision('Red_1', PEER_HOST) },
} satisfies Frame;

export function createWorkbenchFixture() {
  return structuredClone({
    config, run, frame,
    capabilities: {
      default_config: config, engine_interpreter_available: false,
      profiles: [{ id: config.scenario.profile, name: 'TEST/MOCK profile', qualification: 'Synthetic UI fixture only', engine_interpreter_available: false }],
    },
  });
}
