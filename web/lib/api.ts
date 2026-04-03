const API = process.env.NEXT_PUBLIC_API_URL!;

export interface UserInfo {
  id: number;
  username: string;
  referral_code: string;
  wallet_address: string | null;
  tokens: number;
  total_earned: number;
  claimed_tokens: number;
  last_claim_at: string | null;
  created_at: string;
}

export interface NodeInfo {
  node_id: string;
  device_id: string;
  uptime: number;
  last_seen: string;
  status: string;
  node_score: number;
  ip_address: string | null;
}

export interface ChainNodeInfo {
  chain_node_id: string;
  chain_id: number;
  chain_name: string;
  last_block: number;
  sync_lag: number;
  status: string;
  last_verified: string | null;
}

export interface TokensInfo {
  username: string;
  tokens: number;
  total_earned: number;
  claimed_tokens: number;
  last_claim_at: string | null;
}

export async function getUser(username: string): Promise<UserInfo | null> {
  const r = await fetch(`${API}/user/${username}`, { cache: "no-store" });
  if (!r.ok) return null;
  return r.json();
}

export async function getTokens(username: string): Promise<TokensInfo | null> {
  const r = await fetch(`${API}/tokens/${username}`, { cache: "no-store" });
  if (!r.ok) return null;
  return r.json();
}

export async function claimTokens(username: string): Promise<{
  amount: string;
  nonce: string;
  deadline: number;
  v: number;
  r: string;
  s: string;
  contract: string;
  chain_id: number;
  pending_amount: number;
}> {
  const r = await fetch(`${API}/tokens/prepare-claim`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username }),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || "Failed to prepare claim");
  return data;
}

export async function confirmClaim(username: string, tx_hash: string, amount: number): Promise<void> {
  await fetch(`${API}/tokens/confirm-claim`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, tx_hash, amount }),
  });
}

export async function getUserNodes(username: string): Promise<NodeInfo[]> {
  const r = await fetch(`${API}/node/user/${username}`, { cache: "no-store" });
  if (!r.ok) return [];
  return r.json();
}

export async function getChainNodes(nodeId: string): Promise<ChainNodeInfo[]> {
  const r = await fetch(`${API}/chain/nodes/${nodeId}`, { cache: "no-store" });
  if (!r.ok) return [];
  return r.json();
}

export async function linkWallet(username: string, walletAddress: string): Promise<UserInfo | null> {
  const r = await fetch(`${API}/user/${username}/wallet`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ wallet_address: walletAddress }),
  });
  if (!r.ok) {
    const err = await r.json();
    throw new Error(err.detail || "Failed to link wallet");
  }
  return r.json();
}

export interface MiningInfo {
  current_epoch: number;
  current_rate_per_min: number;
  decay_factor: number;
  epoch_duration_days: number;
  days_until_next_decay: number;
  total_distributed: number;
  mining_supply_cap: number;
  remaining_supply: number;
  supply_exhausted: boolean;
}

export interface ExplorerNode {
  node_id: string;
  username: string;
  uptime: number;
  last_seen: string;
  node_score: number;
  ip_address: string;
  status: string;
}

export interface NetworkStats {
  active_nodes: number;
  total_users: number;
  total_devices: number;
  total_uptime_hours: number;
}

export async function getExplorerNodes(): Promise<ExplorerNode[]> {
  const r = await fetch(`${API}/explorer/nodes`, { cache: "no-store" });
  if (!r.ok) return [];
  return r.json();
}

export async function getNetworkStats(): Promise<NetworkStats | null> {
  const r = await fetch(`${API}/explorer/stats`, { cache: "no-store" });
  if (!r.ok) return null;
  return r.json();
}

export async function getMiningInfo(): Promise<MiningInfo | null> {
  const r = await fetch(`${API}/mining/info`, { cache: "no-store" });
  if (!r.ok) return null;
  return r.json();
}

export async function getSupportedChains() {
  const r = await fetch(`${API}/chain/supported`, { cache: "force-cache" });
  if (!r.ok) return [];
  return r.json();
}

export function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export function timeAgo(dateStr: string): string {
  const diff = (Date.now() - new Date(dateStr).getTime()) / 1000;
  if (diff < 60) return `${Math.floor(diff)}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}
