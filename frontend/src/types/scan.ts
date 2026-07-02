export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';

export interface Finding {
  title: string;
  description: string;
  severity: Severity;
  affected_component: string;
  recommendation: string;
}

export interface ScanSummary {
  total_findings: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

export interface SecurityHeaderPresent {
  name: string;
  value: string;
  explanation: string;
}

export interface SecurityHeaderMissing {
  name: string;
  explanation: string;
  recommendation: string;
}

export interface OpenPort {
  port: number;
  protocol: string;
  state: string;
  service: string;
}

export interface FrontendLibraryHint {
  name: string;
  version?: string | null;
  source: string;
  confidence: string;
  status: string;
}

export interface CookieResult {
  name: string;
  secure: boolean;
  httponly: boolean;
  samesite: string | null;
  expires: string;
  domain: string;
  path: string;
}

export interface CookieSummary {
  missing_secure: number;
  missing_httponly: number;
  missing_samesite: number;
}

export interface ScanChecks {
  ssl?: Record<string, unknown>;
  headers?: {
    ok?: boolean;
    status_code?: number;
    present?: SecurityHeaderPresent[];
    missing?: SecurityHeaderMissing[];
    error?: string;
  };
  redirect?: Record<string, unknown>;
  server_leakage?: Record<string, unknown>;
  ports?: {
    ok?: boolean;
    nmap_available?: boolean;
    command?: string;
    open_ports?: OpenPort[];
    error?: string | null;
  };
  libraries?: {
    ok?: boolean;
    libraries?: FrontendLibraryHint[];
    error?: string;
  };
  cookies?: {
    ok?: boolean;
    cookies_found?: number;
    results?: CookieResult[];
    summary?: CookieSummary;
    status?: string;
    error?: string;
  };
}

export interface ScanReport {
  id: number;
  target_url: string;
  scan_date: string;
  risk_score: number;
  grade: string;
  summary: ScanSummary;
  checks: ScanChecks;
  findings: Finding[];
  recommendations: string[];
}

export interface ScanHistoryItem {
  id: number;
  target_url: string;
  scan_date: string;
  risk_score: number;
  grade: string;
  total_findings: number;
}
