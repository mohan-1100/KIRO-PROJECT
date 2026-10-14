export type ComponentType = 'web_application' | 'api_service' | 'database' | 'cache' | 'authentication_service' | 'message_queue' | 'payment_service' | 'external_api' | 'load_balancer';
export type Criticality = 'low' | 'medium' | 'high' | 'critical';
export type HealthStatus = 'healthy' | 'degraded' | 'failed' | 'unknown';
export type EvidenceSource = 'manually_entered' | 'auto_discovered' | 'inferred' | 'simulated_demo' | 'unknown';
export type ConfirmationStatus = 'confirmed' | 'inferred' | 'unknown';
export type FailureType = 'component_unavailable' | 'component_degraded' | 'dependency_link_unavailable';
export type TargetType = 'component' | 'edge';
export type IncidentStatus = 'open' | 'resolved';

export interface Scenario { id: string; name: string; description: string | null; created_at: string; }

export interface Component {
  id: string; scenario_id: string; name: string; type: ComponentType;
  criticality: Criticality; health_status: HealthStatus;
  last_observed_at: string | null; evidence_source: EvidenceSource;
  confirmation_status: ConfirmationStatus; data_quality_score: number;
}

export interface Edge {
  id: string; scenario_id: string; source_component_id: string; target_component_id: string;
  label: string | null; evidence_source: EvidenceSource;
  confirmation_status: ConfirmationStatus; last_observed_at: string | null;
}

export interface Graph { scenario_id: string; components: Component[]; edges: Edge[]; }

export interface ScoreBreakdown {
  label: string;
  criticality_score: { value: number; weight: number };
  reach_score: { value: number; weight: number };
  proximity_score: { value: number; weight: number };
  isolation_score: { value: number; weight: number };
}

export interface AffectedComponentSummary {
  component_id: string; name: string; criticality: Criticality;
  severity_contribution: number; has_alternative_path: boolean;
  possible_alternative_sources: string[];
}

export interface PathStep { component_id: string; component_name: string; edge_direction: string | null; }

export interface ImpactPath {
  affected_component_id: string; affected_component_name: string;
  path_steps: PathStep[]; explanation_text: string;
  has_dq_warning: boolean; alternative_paths: PathStep[][];
}

export interface PossibleAltPathComponent {
  component_id: string; component_name: string;
  possible_alternative_source_names: string[]; disclosure: string;
}

export interface StalenessWarning { component_id: string; component_name: string; hours_since_observed: number; }

export interface ImpactReport {
  sim_id: string; scenario_id: string; failed_target_id: string;
  failed_target_type: TargetType; failure_type: FailureType;
  impact_score: number; data_confidence_score: number;
  score_breakdown: ScoreBreakdown; low_confidence_notice: string | null;
  already_failed_warning: boolean;
  directly_affected: AffectedComponentSummary[];
  transitively_affected: AffectedComponentSummary[];
  impact_paths: ImpactPath[];
  possible_alt_path_components: PossibleAltPathComponent[];
  staleness_warnings: StalenessWarning[];
  simulated_projection_label: string | null; timestamp: string;
}

export interface SimulationHistoryRecord {
  id: string; scenario_id: string; timestamp: string;
  failed_target_id: string; failed_target_type: TargetType;
  failure_type: FailureType; directly_affected_count: number;
  transitively_affected_count: number; impact_score: number;
  data_confidence_score: number; status: IncidentStatus;
}

export interface RecoveryOption {
  recovery_target_id: string; recovery_type: TargetType;
  services_recovered: string[]; services_recovered_count: number;
  services_still_affected: string[]; services_still_affected_count: number;
  projected_impact_score: number; simulated_projection_label: string;
  disclosure: string; no_additional_recovery: boolean;
}

export interface RecoveryResponse { options: RecoveryOption[]; simulated_projection_label: string; }

export interface DataQualityComponent {
  component_id: string; name: string; type: ComponentType; criticality: Criticality;
  evidence_source: EvidenceSource; confirmation_status: ConfirmationStatus;
  data_quality_score: number; last_observed_at: string | null;
  is_stale: boolean; hours_since_observed: number | null;
}

export interface DataQualityEdge {
  edge_id: string; source_component_id: string; target_component_id: string;
  label: string | null; evidence_source: EvidenceSource;
  confirmation_status: ConfirmationStatus; last_observed_at: string | null;
  is_stale: boolean; hours_since_observed: number | null;
}

export interface DataQuality {
  scenario_id: string; data_completeness_indicator: number;
  freshness_threshold_hours: number;
  components: DataQualityComponent[]; edges: DataQualityEdge[];
}

export interface Settings { freshness_threshold_hours: number; }

export interface SimulationOverlay {
  simId: string; failedTargetId: string; failedTargetType: TargetType;
  failureType: FailureType; affectedComponentIds: string[];
  possibleAltComponentIds: string[]; impactReport: ImpactReport;
}
