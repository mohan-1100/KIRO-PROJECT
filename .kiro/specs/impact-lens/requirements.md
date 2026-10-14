# Requirements Document

## Introduction

ImpactLens is a web-based Explainable Network Dependency and Outage Impact Simulator. It enables
software engineers to visualize infrastructure dependency graphs, simulate component failures,
automatically identify all affected services, and understand *why* each service is affected
through traceable dependency chains.

The platform operates entirely on simulated infrastructure data — no real cloud account or AWS
credentials are required. It is designed to look and feel like a professional observability
tool (comparable in quality to Amazon CloudWatch or Azure Application Insights, but not a copy
of them).

ImpactLens answers six questions during any incident:

1. What component failed?
2. Which services are affected (directly or indirectly)?
3. Why is each service affected?
4. What alternative dependency paths remain available?
5. What recovery options could restore the most services?
6. How complete and trustworthy is the dependency information?

### Educational Note: Dependency Direction Convention

Throughout this document, an edge **A → B** means "B depends on A". In graph theory terms, an
edge points *from the dependency to the dependent*. Concretely: if `PaymentAPI → OrderService`,
then `OrderService` depends on `PaymentAPI` — if `PaymentAPI` fails, `OrderService` is potentially
affected.

This convention is consistent with how tools like Backstage and ServiceGraph represent
infrastructure. Engineers reading the diagram should ask: "If the node at the tail of the arrow
fails, the node at the head of the arrow is at risk."

---

## Glossary

- **Component**: Any infrastructure element modelled in ImpactLens — web apps, APIs, databases,
  caches, auth services, message queues, payment services, external APIs, or load balancers.
- **Edge**: A directed dependency relationship between two Components.
- **Dependant**: A Component that depends (directly or indirectly) on a given Component.
- **Dependency**: A Component on which another Component relies.
- **Scenario**: A named, saved configuration of Components and Edges owned by that Scenario. Each Scenario maintains its own baseline graph and baseline health states for all its Components. A Component or Edge belongs to exactly one Scenario.
- **Scenario Picker**: A dropdown control in the persistent top bar that lists all available Scenarios returned by GET /scenarios. On first visit, THE Frontend SHALL automatically select the first Scenario in the list (ordered by created_at ascending). When a user selects a different Scenario, THE Frontend SHALL (1) clear the previous Scenario's simulation overlay from the display without issuing a reset to the API_Server, (2) fetch the selected Scenario's baseline graph, (3) check for an existing Active Simulation on the selected Scenario and display its overlay if present, and (4) update the Scenario Picker label to the newly selected Scenario name. The Frontend SHALL always pass the currently selected scenario_id as a path parameter to all scenario-scoped API endpoints.
- **Active Simulation**: Server-side ephemeral state stored in memory (not persisted to the DB) representing a failure experiment applied on top of the active Scenario's baseline. At most one Active Simulation may exist per Scenario at any time. The Active Simulation is lost if the API_Server restarts; on restart the frontend detects the absence of Active Simulation state and clears any simulation overlay, returning to the baseline Scenario view.
- **Incident**: A simulation event that has been recorded to Simulation_History and carries a resolved impact report and a status value (one of: open, resolved). An Incident is created automatically when a simulation completes. The active incident count shown on the Overview page is the count of Incident records whose status is "open". An Incident's status is set to "resolved" when the user resets the simulation or explicitly marks it resolved.
- **Criticality**: An engineer-assigned priority level for a Component indicating its business importance. Permitted values and their numeric weights used in all ImpactLens scoring formulas are: low (weight 1), medium (weight 2), high (weight 3), critical (weight 4). If a Component has no criticality assigned, it defaults to low (weight 1).
- **Simulation**: An ephemeral failure experiment applied on top of a Scenario's baseline graph. A Simulation targets either a single Component (failure types: component_unavailable, component_degraded) or a single directed Edge (failure type: dependency_link_unavailable). A Simulation does not alter the Scenario's stored baseline unless the user explicitly saves it as a new Scenario.
- **Dependency Link Failure**: A Simulation failure type that marks a single directed Edge as absent for the duration of the Active Simulation. Both endpoint Components retain their current baseline health status unchanged. When the Active Simulation is reset, the Edge is restored to its original state automatically. At most one Edge may be disabled per Simulation in the initial version.
- **Impact Score**: A numeric heuristic in the range 0–100 computed by the ImpactLens Impact Score Formula (see Requirement 4) representing the operational blast radius of a Component failure. The Impact Score reflects graph topology and criticality. Data confidence is reported separately as a Data Confidence Score and does NOT reduce the Impact Score value.
- **Data Confidence Score**: A numeric value in the range 0–100 reported alongside the Impact Score in every impact report. It reflects the average data_quality_score of all Components involved in the impact analysis. A low Data Confidence Score means the Impact Score conclusions should be treated with caution, but the Impact Score itself is not reduced.
- **Data Quality Warning Threshold**: A fixed constant of 50. When any Component involved in an impact path has a data_quality_score below 50, the Impact_Engine annotates that Component's explanation with a data quality uncertainty notice. This threshold is not user-configurable in the initial version.
- **Impact Path**: The ordered chain of dependency edges that explains why a specific service is
  affected by a failure.
- **Alternative Path**: A traversal route from a Dependant back to a healthy dependency that satisfies the same role as the failed Component, evaluated using the following conservative rule:

  Given the A → B edge convention (B depends on A), when Component F fails:
  1. For each Component D in the impacted candidate set (reachable from F via dependant edges), find all inbound edges to D that do NOT pass through F or any failed Edge.
  2. If at least one such inbound path exists and the source of that path is a non-failed Component, D is considered to have a valid Alternative Path and is excluded from the impacted set.
  3. If no such path exists, D is marked as affected.

  **Important limitation**: ImpactLens does not model whether two paths provide equivalent capabilities (e.g., two databases with different data). The model conservatively treats any non-failed inbound path as a valid alternative. Engineers must verify operational equivalence separately. This limitation is always disclosed in the impact report when an Alternative Path is identified.
- **Evidence Source**: The origin of a piece of dependency metadata (e.g., manually entered,
  auto-discovered, inferred).
- **Freshness Threshold**: The configurable maximum age (in hours) of dependency metadata before
  it is considered stale.
- **Data Quality Score**: A per-Component or per-Edge metric (0–100) reflecting completeness and
  recency of available evidence.
- **Graph_Engine**: The backend NetworkX-based service that performs graph traversal, impact
  analysis, and path finding.
- **API_Server**: The FastAPI backend that exposes all application endpoints.
- **DB**: The SQLite database auto-created on backend startup.
- **Seed_Loader**: The component that inserts demo data into an empty DB on startup.
- **Frontend**: The React/TypeScript/Vite single-page application.
- **Dependency_Map**: The page that renders the interactive React Flow canvas.
- **Impact_Engine**: The module that computes Impact Scores, Impact Paths, and warnings.
- **Recovery_Planner**: The page and backend module that evaluates recovery scenarios.
- **Simulation_History**: The persisted log of completed simulations recorded in the DB. Records are retained indefinitely and survive server restarts. Each record corresponds to one Incident.
- **Settings_Panel**: The application page for freshness threshold and data quality configuration.

---

## Requirements

---

### Requirement 1: Interactive Dependency Graph Visualization

**User Story:** As an engineer, I want to view my infrastructure as an interactive directed graph
so that I can immediately understand which components depend on which other components.

> **Why this matters (educational note):** A directed graph is the natural data structure for
> infrastructure dependencies. Libraries like NetworkX (Python) and React Flow (TypeScript) are
> built specifically to work with graphs. React Flow handles the visual canvas; NetworkX handles
> the mathematical traversal. Keeping them in separate layers (frontend vs. backend) follows the
> single-responsibility principle.

#### Acceptance Criteria

1. THE Dependency_Map SHALL render all Components as nodes on a React Flow canvas with pan and
   zoom controls, supporting zoom levels from 10% to 200% of the default view.
2. THE Dependency_Map SHALL render all Edges as directed arrows from dependency to dependant,
   consistent with the A → B convention defined in the Glossary.
3. WHEN a user clicks a node, THE Dependency_Map SHALL open a details panel displaying the
   Component's name, type, health status, criticality, evidence source, last observed time, and
   Data Quality Score.
4. THE Dependency_Map SHALL support the following Component types as distinct visual node shapes
   or icons: web application, API service, database, cache, authentication service, message
   queue, payment service, external API, and load balancer.
5. THE Dependency_Map SHALL display each Component's health status using both a labelled badge
   and a distinct icon or shape — the status SHALL NOT be communicated by color alone — to
   ensure accessibility for users with color vision deficiency.
6. THE Dependency_Map SHALL support four health status values: healthy, degraded, failed, and
   unknown.
7. WHEN a user applies a filter by Component type, THE Dependency_Map SHALL display only nodes
   matching the selected type and their connecting edges within 500 milliseconds of the filter
   being applied.
8. WHEN a user applies a filter by health status, THE Dependency_Map SHALL display only nodes
   matching the selected status and their connecting edges within 500 milliseconds of the filter
   being applied.
9. WHEN a user applies a filter by criticality level, THE Dependency_Map SHALL display only
   nodes matching the selected criticality and their connecting edges within 500 milliseconds of
   the filter being applied.
10. WHEN a user types a search term of 1 to 200 characters into the search field, THE
    Dependency_Map SHALL highlight all nodes whose names contain the search term
    (case-insensitive) and scroll the canvas to bring at least one matching node into view
    within 500 milliseconds.
11. IF no nodes match the active filters or search term, THEN THE Dependency_Map SHALL display
    a "No matching components" message in the canvas area while preserving the current pan and
    zoom position.
12. IF the Dependency_Map fails to load graph data from the API_Server, THEN THE Dependency_Map
    SHALL display an error indicator in the canvas area and provide a retry control that
    re-requests the graph data.

---

### Requirement 2: Component and Edge Management

**User Story:** As an engineer, I want to add, edit, and remove components and dependency edges
so that I can keep the dependency model accurate as infrastructure evolves.

#### Acceptance Criteria

1. WHEN a user submits a valid new-component form, THE API_Server SHALL create the Component in
   the DB and return the created Component with its assigned identifier within 2 seconds.
2. IF a user submits a new-component form with a missing required field (name, type, or
   criticality), THEN THE API_Server SHALL return a 422 validation error with a field-level
   message identifying each missing or invalid field without creating any Component record.
3. IF a user submits a new-component form where the component name matches an existing Component
   name (case-insensitive) in the same scenario, THEN THE API_Server SHALL return a 409 conflict
   error indicating the duplicate name without creating any Component record.
4. WHEN a user submits a valid component-edit form, THE API_Server SHALL update the Component in
   the DB and return the updated Component within 2 seconds.
5. IF a user submits a component-edit form with a missing required field (name, type, or
   criticality), THEN THE API_Server SHALL return a 422 validation error with a field-level
   message identifying each missing or invalid field without modifying the existing Component
   record.
6. WHEN a user requests deletion of a Component that has no outbound or inbound Edges, THE
   API_Server SHALL delete the Component and return a 200 confirmation within 2 seconds.
7. IF a user requests deletion of a Component that has at least one associated Edge, THEN THE
   API_Server SHALL return a 409 conflict error listing the identifiers of all affected Edges
   without deleting the Component or any associated Edge.
8. IF a user submits a new-edge form where source equals target, THEN THE API_Server SHALL
   return a 422 validation error indicating self-loops are not permitted without creating any
   Edge record.
9. IF a user submits a new-edge form where the combination of source identifier and target
   identifier already exists as an Edge in the same scenario, THEN THE API_Server SHALL return a
   409 conflict error indicating the duplicate edge without creating any Edge record.
10. WHEN a user submits a valid new-edge form (source and target are different Components, edge
    does not already exist), THE API_Server SHALL create the Edge in the DB and return the
    created Edge with its assigned identifier within 2 seconds.
11. WHEN a user submits a valid edge-edit form, THE API_Server SHALL update the Edge metadata
    (label and evidence source) in the DB, preserve the original source and target identifiers
    unchanged, and return the updated Edge within 2 seconds.
12. IF a user submits an edge-edit form with a missing required metadata field, THEN THE
    API_Server SHALL return a 422 validation error with a field-level message identifying each
    missing or invalid field without modifying the existing Edge record.
13. WHEN a user requests deletion of an Edge, THE API_Server SHALL delete the Edge from the DB
    and return a 200 confirmation within 2 seconds.
14. WHEN THE Frontend receives a successful API response for any component or edge create,
    update, or delete operation, THE Frontend SHALL reflect the change in the Dependency_Map
    canvas within one re-render cycle.

---

### Requirement 3: Failure Simulation

**User Story:** As an engineer, I want to simulate component failures so that I can understand
the blast radius before an incident occurs rather than during one.

> **Educational note:** Simulations are *ephemeral* — they create a temporary overlay on the
> baseline graph without mutating the stored state. This is the same pattern used by game engines
> (a "what-if" branch). Saving the simulation as a new Scenario is an explicit, opt-in action.

#### Acceptance Criteria

1. WHEN a user selects a failure target and submits the simulation request, THE Frontend SHALL send POST /scenarios/{scenario_id}/simulations with a JSON body containing: scenario_id (UUID of the active Scenario), target_type (enum: "component" or "edge"), target_id (UUID of the target Component or Edge), and failure_type (enum: "component_unavailable" or "component_degraded" when target_type is "component"; "dependency_link_unavailable" when target_type is "edge"). THE API_Server SHALL validate that target_id belongs to the given scenario_id and return a 404 error if it does not. On success, THE API_Server SHALL store the Active Simulation state in server memory and return a full impact report without modifying the baseline Scenario in the DB.
2. THE API_Server SHALL enforce the following failure_type constraints:
   a. "component_unavailable" — valid only when target_type is "component"; marks the target Component as failed for traversal purposes; all inbound and outbound edges of that Component are treated as severed during impact traversal.
   b. "component_degraded" — valid only when target_type is "component"; marks the target Component as degraded; inbound and outbound edges remain traversable but the Component's health is recorded as degraded in the simulation overlay.
   c. "dependency_link_unavailable" — valid only when target_type is "edge"; marks the target Edge as absent for traversal purposes; both endpoint Components retain their baseline health status.
   IF a request combines an invalid target_type and failure_type pair, THE API_Server SHALL return a 422 error identifying the invalid combination without creating an Active Simulation.
3. WHILE a simulation is running, THE Frontend SHALL display a persistent "Simulation Active" indicator in the top bar. WHEN the simulation target is a Component, the indicator SHALL show the Component name and failure type. WHEN the simulation target is an Edge, the indicator SHALL show the source Component name, the target Component name, and "dependency link unavailable".
4. WHEN a user clicks "Reset Simulation", THE API_Server SHALL clear the Active Simulation state from server memory (including any failed-edge state) and THE Frontend SHALL clear the simulation overlay and restore all nodes and edges to their baseline health status without requiring a page reload. The reset SHALL NOT modify any record in the edges table in the DB.
5. WHEN a user explicitly clicks "Save Simulation as Scenario" and provides a non-empty unique scenario name, THE API_Server SHALL create a new independent Scenario in the DB by copying the active Scenario's current baseline graph (all Components and Edges, with their baseline health statuses) into the new Scenario. The new Scenario SHALL be independent of the original — subsequent changes to either Scenario SHALL NOT affect the other. The simulated failure state SHALL NOT be written into the new Scenario's baseline health statuses; the new Scenario captures only the baseline topology. THE API_Server SHALL return the newly created Scenario with its assigned identifier.
6. IF a user clicks "Save Simulation as Scenario" without providing a name, THEN THE Frontend
   SHALL display a validation error and SHALL NOT send the save request to the API_Server.
7. THE API_Server SHALL record each completed simulation to the Simulation_History in the DB with: a unique identifier, a timestamp, the failed Component or Edge identifier, the failure type, the count of directly and transitively affected Components, the Impact Score, the Data Confidence Score, and an initial status of "open".
8. IF a simulation targets a Component whose status is already "failed" in the baseline, THEN
   THE API_Server SHALL proceed with the simulation and include a warning in the response noting
   that the Component was already marked failed.
9. IF a simulation request references a Component or Edge identifier that does not exist in the given Scenario in the DB, THEN THE API_Server SHALL return a 404 error identifying the missing target (specifying whether it was a Component or Edge) without creating a simulation record.
10. IF the API_Server restarts while an Active Simulation is in progress, THEN the Active Simulation state SHALL be lost; WHEN the Frontend next polls for Active Simulation state and receives an empty response, THE Frontend SHALL clear the simulation overlay and display a notification informing the user that the simulation was cleared due to a server restart.
11. THE simulation_history record created by a completed simulation SHALL set failed_target_type to "component" or "edge" matching the target_type of the simulation request, and SHALL set failed_target_id to the target_id of the simulation request, so that history records unambiguously identify whether a Component or an Edge was the simulation target.
12. WHEN a new Scenario is created via "Save Simulation as Scenario", THE API_Server SHALL NOT modify the original Scenario's Components, Edges, or baseline health statuses. The original Scenario's Active Simulation, if any, SHALL remain unchanged. The Scenario Picker SHALL include the new Scenario in its list immediately after creation.

---

### Requirement 4: Automatic Impact Identification and Ranking

**User Story:** As an engineer, I want the system to automatically find all directly and
indirectly affected services when a failure occurs, so that I do not have to trace the graph
manually.

> **Educational note:** Impact identification uses a *graph traversal* — specifically a modified
> breadth-first search (BFS) from the failed node, following edges in the dependant direction.
> NetworkX's `descendants()` function provides this, but the Impact_Engine adds additional logic
> to handle failed edges, alternative paths, and cycle safety. Cycles can exist in real
> infrastructure (mutual dependencies are an anti-pattern but do occur), and BFS with a visited
> set handles them without infinite loops.

#### Acceptance Criteria

1. WHEN a simulation is executed, THE Impact_Engine SHALL traverse the dependency graph from the
   failed Component, following edges in the dependant direction, to identify all direct and
   indirect Dependants, completing traversal within 5 seconds for graphs containing up to 10,000
   nodes and 50,000 edges.
2. THE Impact_Engine SHALL correctly distinguish direct Dependants (exactly one edge away from
   the failed Component) from indirect Dependants (two or more edges away from the failed
   Component) and label each accordingly in the impact report.
3. THE Impact_Engine SHALL apply the Alternative Path rule defined in the Glossary to determine whether a reachable Dependant is excluded from the impacted set. A Dependant is excluded if and only if: at least one inbound edge to that Dependant (in the A → B dependency direction) originates from a Component that is not the failed Component and is not reached exclusively through failed Edges, and that source Component is not itself in the impacted set due to the current simulation. If no such inbound edge exists, the Dependant is included in the impacted set. THE Impact_Engine SHALL always include a disclosure in the impact report when a Component is excluded due to an Alternative Path, stating: "Alternative path detected — operational equivalence not verified. Engineer review recommended."
4. THE Impact_Engine SHALL handle cycles in the dependency graph without entering an infinite
   loop by maintaining a visited-node set during traversal, ensuring each node is processed at
   most once per simulation run.
5. THE Impact_Engine SHALL exclude failed Edges from traversal paths, treating them as absent
   from the graph for the duration of the simulation.
6. WHEN a traversal path to a Component passes exclusively through nodes that have no directed
   edge relationship to the failed Component's subgraph, THE Impact_Engine SHALL NOT mark that
   Component as affected.
7. THE Impact_Engine SHALL compute an Impact Score in the range 0–100 (inclusive) for the
   failed Component using the ImpactLens Impact Score Formula:

   Step 1 — Compute per-factor normalized scores (each 0.0–1.0):
     criticality_score    = criticality_weight / 4          (weight from Criticality Glossary entry)
     reach_score          = min(affected_count, 20) / 20    (capped at 20 dependants)
     proximity_score      = 1 / (1 + avg_hop_distance)      (avg hops from failed node to affected nodes; 0 if no dependants)
     isolation_score      = 1 − alt_path_ratio              (ratio of affected nodes that have at least one valid alternative path)

   Step 2 — Weighted sum:
     raw_score = (criticality_score × 0.35)
               + (reach_score       × 0.30)
               + (proximity_score   × 0.20)
               + (isolation_score   × 0.15)

   Step 3 — Scale to 0–100 and clamp:
     impact_score = min(100, round(raw_score × 100))

   This formula is labelled "ImpactLens heuristic v1.0 — not an industry standard metric". The weights (0.35, 0.30, 0.20, 0.15) are documented assumptions and may be revised in future versions.
8. THE Impact_Engine SHALL include in every impact report:
   a. The Impact Score (integer 0–100) computed by the ImpactLens Impact Score Formula.
   b. A Data Confidence Score (integer 0–100) computed as the arithmetic mean of the data_quality_score of all Components involved in the impact analysis, rounded to the nearest integer. If no Components are involved, the Data Confidence Score is 100.
   c. A human-readable breakdown showing each formula factor's name, its computed normalized value, and its weight, labelled "ImpactLens heuristic v1.0 — not an industry standard metric".
   d. A plain-language confidence notice when the Data Confidence Score is below 50, stating: "Data confidence is low — impact conclusions may be incomplete due to missing or stale dependency information."
9. THE Impact_Engine SHALL sort the list of affected Components in the impact report in
   descending order of each Component's individual severity contribution score, calculated as:
   severity_contribution = criticality_weight × (1 − alt_path_ratio_for_this_component)
   Ties SHALL be broken by Component name in ascending alphabetical order.
10. THE Impact_Engine SHALL deduplicate affected Components so that each Component appears at
    most once in the impact report regardless of how many traversal paths reach it.
11. IF the dependency graph contains no outbound edges from the failed Component in the
    dependant direction, THEN THE Impact_Engine SHALL return an impact report with an empty
    affected-Components list and an Impact Score of 0.
12. IF graph traversal does not complete within 5 seconds for the given graph, THEN THE
    Impact_Engine SHALL abort traversal and return a timeout error response, without returning a
    partial impact report.
13. THE Impact_Engine SHALL compute the Data Confidence Score independently of the Impact Score. A low Data Confidence Score SHALL NOT reduce the Impact Score value. Both scores SHALL be reported separately in the impact report so that a high-severity failure on poorly-documented infrastructure shows a high Impact Score alongside a low Data Confidence Score.
14. WHEN the simulation target is an Edge (failure_type: dependency_link_unavailable), THE Impact_Engine SHALL compute the Impact Score using the same four-factor formula as for Component failures, with the following substitution for criticality_score: use the maximum criticality_weight of the two endpoint Components of the failed Edge divided by 4. All other formula factors (reach_score, proximity_score, isolation_score) are computed from the resulting impacted set as normal.

---

### Requirement 5: Explainable Impact Paths

**User Story:** As an engineer, I want to see exactly *why* each service is affected — the full
dependency chain from the failed component to the affected service — so that I can explain the
incident to stakeholders without guessing.

#### Acceptance Criteria

1. WHEN an impact report is generated, THE Impact_Engine SHALL include at least one Impact Path
   for every affected Component showing the ordered chain of edges from the failed Component to
   that Component, where each step lists the Component name and the edge direction.
2. THE Impact_Engine SHALL generate human-readable explanations for each Impact Path using
   template-based text, completing rendering within 500 milliseconds of the Impact Path data
   being available, with no large language model or external AI service required.
3. THE Impact_Engine SHALL distinguish direct impact explanations (where the affected Component
   has exactly one edge from the failed Component) from indirect impact explanations (where the
   affected Component is separated by two or more edges), producing distinct explanation text
   for each case.
4. WHEN a Component has Alternative Paths, THE Impact_Engine SHALL include each Alternative
   Path in the explanation text and label each one as "available alternative route".
5. WHEN a Component in an Impact Path has a data_quality_score below 50 (the fixed Data Quality Warning Threshold), THE Impact_Engine SHALL annotate that Component's explanation with an uncertainty notice stating: "dependency data quality for [Component name] is low (score: [score]) — impact conclusions for this path may be incomplete."
6. THE Frontend SHALL render each Impact Path explanation in the details panel as an expandable
   section, defaulting to collapsed when more than three Impact Paths exist for the selected
   Component, and defaulting to expanded when three or fewer Impact Paths exist.
7. WHEN a user clicks an explanation entry, THE Frontend SHALL visually highlight all edges and
   nodes belonging to the corresponding Impact Path on the Dependency_Map canvas within 300
   milliseconds, and restore the previous visual state when the user deselects the entry.
8. IF the Impact_Engine cannot construct a complete ordered chain of edges from the failed
   Component to an affected Component, THEN THE Impact_Engine SHALL omit that Impact Path from
   the report and include an entry in the report indicating which Component's path could not be
   resolved.

---

### Requirement 6: Alternative Path and Recovery Analysis

**User Story:** As an engineer, I want to understand which recovery actions would restore the
most services, so that I can prioritise incident response without guessing.

> **Educational note:** Recovery analysis is a *what-if* planning tool — it does NOT execute
> any real recovery action. The system models recovery as restoring a failed Component to healthy
> and re-running impact traversal. This is analogous to a "reverse simulation". Comparing
> multiple recovery scenarios is equivalent to comparing subsets of a solution space, a technique
> used in operations research.

#### Acceptance Criteria

1. WHEN a simulation is active and the simulation target is a Component, THE Recovery_Planner SHALL enumerate all currently failed or degraded Components in the active simulation as candidate recovery targets. WHEN a simulation is active and the simulation target is an Edge (failure_type: dependency_link_unavailable), THE Recovery_Planner SHALL present one candidate recovery option: "Restore failed edge [source → target]". Recovery analysis for edge-failure simulations is limited to restoring the single failed Edge in the initial version; Component-level recovery candidates are not enumerated for edge-failure simulations.
2. WHEN a user requests a recovery scenario for a candidate Component, THE API_Server SHALL simulate restoring that Component to its baseline health status, re-run impact traversal using the same simulation parameters, and return the projected impact report. WHEN a user requests recovery of the failed Edge in an edge-failure simulation, THE API_Server SHALL simulate restoring that Edge to present (removing it from the failed-edge set), re-run impact traversal, and return the projected impact report showing services that would no longer be affected. In both cases, THE API_Server SHALL leave the Active Simulation state unchanged, such that re-fetching GET /scenarios/{scenario_id}/simulation returns the same state as before the recovery request.
3. WHEN a recovery scenario is evaluated, THE Recovery_Planner SHALL display the delta between
   the current simulation and that scenario, showing the count of services recovered and the
   count of services still affected.
4. WHEN multiple recovery scenarios are evaluated, THE Recovery_Planner SHALL rank them in
   descending order by the number of services restored.
5. WHEN a user requests a side-by-side comparison of recovery options, THE Recovery_Planner SHALL display up to four recovery scenarios in a table. For Component-failure simulations, each row shows: candidate Component name, count of services recovered, count of services still affected, and estimated impact score after recovery. For edge-failure simulations, the single row shows: failed Edge identifier (source → target), count of services recovered, count of services still affected, and estimated impact score after recovery.
6. THE API_Server SHALL attach a visible "Simulated Projection" label to every recovery analysis
   result in its response payload, and SHALL NOT initiate any real infrastructure change.
7. IF the restoration of a candidate Component would have no effect on the current impacted set
   (because the services affected have other failing dependencies), THEN THE Recovery_Planner
   SHALL display a "No additional services recovered" notice for that scenario.
8. IF a user requests a recovery scenario for a Component that is not in a failed or degraded
   state at the time of the request, THEN THE API_Server SHALL reject the request with a 400
   error indicating the Component is not a valid recovery candidate.
9. THE Recovery_Planner SHALL display a disclosure notice on every recovery result stating: "Recovery analysis is a simulated projection. It does not account for configuration, data consistency, capacity, or routing factors not represented in the dependency graph."
10. THE API_Server SHALL expose POST /scenarios/{scenario_id}/simulations/{sim_id}/recovery as the endpoint for recovery scenario requests, accepting a JSON body with: recovery_type (enum: "component" or "edge"), recovery_target_id (UUID of the Component to restore, or UUID of the Edge to restore).
11. THE Recovery_Planner page SHALL be disabled (showing a "No active simulation" message) when no Active Simulation exists for the selected Scenario. It SHALL be enabled automatically when a simulation is started.

---

### Requirement 7: Confidence, Evidence, and Data Quality

**User Story:** As an engineer, I want to know how much I can trust the dependency data, so that
I can calibrate my confidence in the impact analysis and flag gaps to my team.

> **Educational note:** In real systems, dependency maps are often incomplete. Services get
> added without registering their dependencies; documentation drifts. ImpactLens models this
> explicitly rather than pretending the graph is complete. The "evidence source" and "last
> observed" fields mirror metadata patterns used by tools like Backstage (software catalog) and
> AWS Service Catalog.

#### Acceptance Criteria

1. THE API_Server SHALL store the following metadata for each Component: last_observed_at
   (ISO-8601 timestamp), evidence_source (one of: manually_entered, auto_discovered, inferred,
   simulated_demo, unknown), confirmation_status (one of: confirmed, inferred, unknown), and
   data_quality_score (integer 0–100).
2. THE API_Server SHALL store the following metadata for each Edge: last_observed_at
   (ISO-8601 timestamp), evidence_source (one of: manually_entered, auto_discovered, inferred,
   simulated_demo, unknown), and confirmation_status (one of: confirmed, inferred, unknown).
3. WHEN the age of a Component's last_observed_at exceeds the configured Freshness Threshold,
   THE API_Server SHALL include a staleness warning for that Component in any impact report that
   references it, identifying the Component by name and the number of hours elapsed since
   last_observed_at.
4. THE Settings_Panel SHALL allow a user to set the Freshness Threshold to any integer value
   between 1 and 8760 hours (1 hour to 1 year), with a default of 72 hours, and SHALL persist
   the configured value so that it applies to all subsequent impact reports until changed.
5. THE Impact_Engine SHALL compute a Data Confidence Score for every impact report as the arithmetic mean of the data_quality_score of all involved Components, rounded to the nearest integer, and SHALL include it in the impact report response alongside the Impact Score. The Data Confidence Score SHALL NOT modify or reduce the Impact Score value.
6. THE Frontend SHALL display a global Data Completeness Indicator on the Overview page showing
   the percentage of Components whose confirmation_status equals "confirmed", calculated as
   (count of confirmed Components / total count of Components) × 100, rounded to the nearest
   whole number.
7. WHEN a Component has confirmation_status of "unknown", THE Dependency_Map SHALL render that
   node with a distinct non-color visual indicator (a dashed border or a question-mark badge) so
   that the indicator remains distinguishable regardless of the node's color.
8. THE API_Server SHALL mark all seed data Components and Edges with evidence_source equal to
   "simulated_demo" and confirmation_status equal to "inferred" so that users can clearly
   distinguish demo data from real entries.
9. IF a request is made to create or update a Component or Edge with a data_quality_score
   outside the range 0–100, THEN THE API_Server SHALL reject the request with a 422 error
   indicating the valid range and leave the existing record unchanged.
10. IF a request is made to create or update a Component or Edge with an evidence_source or
    confirmation_status value not in the defined enumeration, THEN THE API_Server SHALL reject
    the request with a 422 error indicating the accepted values and leave the existing record
    unchanged.
11. THE API_Server SHALL apply the fixed Data Quality Warning Threshold of 50 to all impact path annotations. This threshold is not configurable in the initial version. Any Component with a data_quality_score below 50 that appears in an impact path SHALL trigger an uncertainty annotation in the explanation.

---

### Requirement 8: Sample Data and Demo Scenarios

**User Story:** As an engineer evaluating ImpactLens, I want pre-loaded demo scenarios with
realistic interconnected components, so that I can explore the tool's capabilities without
having to build a topology from scratch.

#### Acceptance Criteria

1. THE Seed_Loader SHALL insert a minimum of 12 fictional Components into an empty DB on first
   startup, covering at least six distinct Component types from the defined type list.
2. THE Seed_Loader SHALL insert the following four named demo Scenarios, each fully
   deterministic and reproducible across restarts:
   a. "Database Failure" — simulates a primary database becoming unavailable and cascading to
      dependent API and web services.
   b. "Shared Dependency Failure" — simulates a shared authentication or cache service failing
      and affecting multiple upstream consumers simultaneously.
   c. "Alternative Path Available" — simulates a failure where at least one Dependant has a
      valid Alternative Path and is therefore not marked as affected.
   d. "Incomplete Evidence" — simulates a failure where one or more Components in the impact
      path have stale or unknown evidence, demonstrating data quality warnings.
3. THE Seed_Loader SHALL NOT re-insert seed data if the DB already contains Component records,
   ensuring idempotent startup behavior.
4. THE Frontend SHALL display the name of the active Scenario in the Scenario Picker in the top bar at all times. IF no Scenario exists in the DB, THE top bar SHALL display "No Scenarios Available".
5. WHEN the Frontend first loads and at least one Scenario exists in the DB, THE Frontend SHALL automatically request and display the first Scenario returned by GET /scenarios (ordered by created_at ascending) without requiring any user action, and SHALL request GET /scenarios/{scenario_id}/simulation to check for an existing Active Simulation for that Scenario. WHEN a user selects a different Scenario from the Scenario Picker, THE Frontend SHALL: (1) clear the previous Scenario's simulation overlay from the display without sending a reset request to the API_Server (the previous Scenario's server-side simulation state is preserved), (2) fetch the selected Scenario's baseline graph from GET /scenarios/{scenario_id}/graph, (3) request GET /scenarios/{scenario_id}/simulation for the selected Scenario and display its simulation overlay if an Active Simulation exists, and (4) render the result on the Dependency_Map within 2 seconds of the selection.

---

### Requirement 9: Backend API

**User Story:** As a developer, I want a well-documented REST API so that the frontend and
future integrations can reliably interact with all application data and logic.

#### Acceptance Criteria

1. THE API_Server SHALL expose CRUD endpoints for Components scoped to a Scenario: POST /scenarios/{scenario_id}/components, GET /scenarios/{scenario_id}/components, GET /scenarios/{scenario_id}/components/{id}, PUT /scenarios/{scenario_id}/components/{id}, DELETE /scenarios/{scenario_id}/components/{id}.
2. THE API_Server SHALL expose CRUD endpoints for Edges scoped to a Scenario: POST /scenarios/{scenario_id}/edges, GET /scenarios/{scenario_id}/edges, GET /scenarios/{scenario_id}/edges/{id}, PUT /scenarios/{scenario_id}/edges/{id}, DELETE /scenarios/{scenario_id}/edges/{id}.
3. THE API_Server SHALL expose a GET /scenarios/{scenario_id}/graph endpoint that returns the full graph (all Components and Edges belonging to that Scenario) in a single response within 2 seconds.
4. THE API_Server SHALL expose POST /scenarios/{scenario_id}/simulations that accepts a JSON body with scenario_id, target_type, target_id, and failure_type as specified in Requirement 3 AC 1, executes the simulation, stores Active Simulation state in server memory, records a Simulation_History entry in the DB, and returns a full impact report.
5. THE API_Server SHALL expose GET /scenarios/{scenario_id}/simulations that returns the Simulation_History records for the given Scenario in reverse-chronological order.
6. THE API_Server SHALL expose POST /scenarios/{scenario_id}/simulations/{sim_id}/recovery that accepts a JSON body with recovery_type and recovery_target_id, runs a projected recovery analysis, and returns the updated impact report without altering the Active Simulation state.
7. THE API_Server SHALL expose POST /scenarios/{scenario_id}/reset that clears the Active Simulation for that Scenario from server memory and returns a 200 confirmation. This endpoint SHALL NOT modify any baseline Component, Edge, or Simulation_History record in the DB.
8. THE API_Server SHALL expose GET /scenarios/{scenario_id}/data-quality that returns per-Component and per-Edge evidence metadata, staleness flags, and the Data Completeness Indicator value for the given Scenario.
9. THE API_Server SHALL validate all request bodies using Pydantic models and return RFC 7807
   Problem Detail JSON for all 4xx and 5xx errors, including a human-readable "detail" field.
10. THE API_Server SHALL serve interactive OpenAPI documentation at /docs and a machine-readable
    schema at /openapi.json.
11. WHEN the API_Server starts, THE DB SHALL be created automatically if it does not exist, and
    THE Seed_Loader SHALL run before the first request is accepted.
12. THE API_Server SHALL expose a GET /scenarios/{scenario_id}/simulation endpoint that returns the current Active Simulation state for that Scenario, or an empty response with status 204 if no Active Simulation exists.
13. THE API_Server SHALL expose scenario management endpoints: GET /scenarios (returns all Scenarios ordered by created_at ascending), POST /scenarios (creates a new Scenario), DELETE /scenarios/{id} (deletes a Scenario and all its Components, Edges, and related Simulation_History records). THE Frontend SHALL read the scenario_id from the Scenario Picker selection and pass it as a path parameter to all scenario-scoped API endpoints (e.g., GET /scenarios/{scenario_id}/graph, POST /scenarios/{scenario_id}/components).
14. THE API_Server SHALL expose a GET /incidents endpoint that returns all Incident records in reverse-chronological order, and a PATCH /incidents/{id} endpoint that accepts a status value of "resolved" to mark an Incident as resolved.
15. THE API_Server SHALL configure CORS to allow cross-origin requests from the configured frontend origin (default: http://localhost:5173) during development, so that the browser does not block API calls from the Vite development server. The allowed origin SHALL be configurable via an environment variable (CORS_ORIGIN) without requiring a code change.

---

### Requirement 10: Database Persistence

**User Story:** As a developer, I want the application to use a self-contained SQLite database
so that the tool runs on any Windows laptop without external database setup.

#### Acceptance Criteria

1. THE DB SHALL be a SQLite file auto-created in the backend working directory on first startup,
   requiring no manual database installation or configuration.
2. THE DB SHALL store the following tables with the columns listed:
   - scenarios: id (UUID), name (text, unique), description (text), created_at (ISO-8601 timestamp).
   - components: id (UUID), scenario_id (FK → scenarios.id), name (text), type (enum), criticality (enum: low, medium, high, critical), health_status (enum: healthy, degraded, failed, unknown), last_observed_at (ISO-8601 timestamp, nullable), evidence_source (enum), confirmation_status (enum), data_quality_score (integer 0–100). Unique constraint on (scenario_id, name) case-insensitively enforced at the application layer.
   - edges: id (UUID), scenario_id (FK → scenarios.id), source_component_id (FK → components.id), target_component_id (FK → components.id), label (text, nullable), evidence_source (enum), confirmation_status (enum), last_observed_at (ISO-8601 timestamp, nullable). No is_failed column — failed-edge state exists only in the in-memory Active Simulation state and is never written to this table.
   - simulation_history: id (UUID), scenario_id (FK → scenarios.id), timestamp (ISO-8601), failed_target_id (text), failed_target_type (enum: component, edge), failure_type (enum), directly_affected_count (integer), transitively_affected_count (integer), impact_score (integer 0–100), data_confidence_score (integer 0–100), status (enum: open, resolved), full_report_json (text).
   Foreign-key relationships SHALL enforce referential integrity.
3. THE DB logic SHALL reside in dedicated database modules that are imported by the API_Server;
   THE Frontend SHALL connect to data exclusively through the API_Server and SHALL NOT access
   the SQLite file directly.
4. WHEN the DB file is deleted and the API_Server is restarted, THE Seed_Loader SHALL recreate
   and reseed the DB, restoring all demo Scenarios and Components within the server startup time.
5. THE DB SHALL enforce a unique constraint on the combination of (scenario_id, source_component_id, target_component_id) for edges, ensuring no duplicate directed dependency relationships exist within the same Scenario.
6. WHEN a simulation is reset or a new Active Simulation replaces the previous one, THE API_Server SHALL clear the failed-edge state from the in-memory Active Simulation object without writing any change to the edges table in the DB, leaving all stored Edge records unmodified.
7. WHEN the API_Server restarts, all Active Simulation state (including any failed-edge state) SHALL be lost because it exists only in server memory. The simulation_history table in the DB SHALL be unaffected by the restart; all previously recorded Simulation_History records SHALL remain accessible after the API_Server comes back online.

---

### Requirement 11: Frontend Application Structure and Navigation

**User Story:** As an engineer, I want a professional dark-themed dashboard with clear
navigation so that I can move between views without losing context.

#### Acceptance Criteria

1. THE Frontend SHALL implement a dark-themed UI with a collapsible left sidebar that contains navigation links to the following eight pages: Overview, Dependency Map, Failure Simulator, Incident Analysis (displaying recorded Incidents from Simulation_History with status tracking), Recovery Planner, Infrastructure Inventory, Simulation History, and Settings & Data Quality.
2. THE Frontend SHALL display a persistent top bar containing: the ImpactLens brand name, a Scenario Picker dropdown (as defined in the Glossary) showing the currently active Scenario name, an environment selector (defaulting to "Simulated Demo"), and the Simulation Active indicator (hidden when no simulation is running).
3. THE Frontend SHALL render a right-side contextual details panel that opens when a node or
   simulation result is selected and closes when the user dismisses it or clicks elsewhere on
   the canvas.
4. THE Frontend SHALL be fully operable on screen widths of 1280 px and above, with no
   horizontal scrollbars or clipped controls at that minimum width.
5. THE Frontend SHALL NOT require authentication or a login screen.

---

### Requirement 12: Overview Dashboard

**User Story:** As an engineer opening ImpactLens, I want an at-a-glance summary of
infrastructure health and active incidents so that I can immediately understand the current
state without navigating to individual pages.

#### Acceptance Criteria

1. THE Frontend SHALL display the following summary metrics on the Overview page, all derived from the API_Server: total Component count (for the active Scenario), healthy Component count, degraded Component count, failed Component count, active incident count (count of Simulation_History records with status "open"), and potentially affected services count (count of Components in the current Active Simulation's impacted set, or 0 if no Active Simulation exists).
2. THE Frontend SHALL derive all summary metrics from the current application state returned by
   the API_Server — no hardcoded values SHALL appear on the Overview page.
3. THE Frontend SHALL display a miniature, non-interactive preview of the Dependency_Map graph
   on the Overview page.
4. THE Frontend SHALL list the three most recently recorded simulation events from
   Simulation_History on the Overview page, each showing the failed Component name, failure
   type, and timestamp.
5. THE Frontend SHALL list the top five Components by criticality weight on the Overview page,
   labelled as "Most Critical Components".
6. THE Frontend SHALL display the global Data Completeness Indicator as a percentage bar on the
   Overview page, using both the numeric percentage and a progress-bar visual.
7. IF the API_Server returns an error when the Overview page fetches its data, THE Frontend
   SHALL display an error notice on the Overview page identifying which metric could not be
   loaded and providing a retry control.

---

### Requirement 13: Infrastructure Inventory

**User Story:** As an engineer, I want a tabular view of all components and their metadata so
that I can audit the dependency model without switching to the graph view.

#### Acceptance Criteria

1. THE Frontend SHALL display all Components in a sortable, filterable table on the
   Infrastructure Inventory page, with columns: name, type, health status, criticality,
   evidence source, confirmation status, data quality score, and last observed.
2. WHEN a user clicks a row in the Infrastructure Inventory table, THE Frontend SHALL navigate
   to the Dependency_Map with that Component selected and its details panel open.
3. THE Frontend SHALL allow inline editing of the evidence_source, confirmation_status, and
   data_quality_score fields directly in the table row without navigating to a separate form.
4. WHEN a user saves an inline edit, THE Frontend SHALL send the update to the API_Server and
   reflect the change in the table without a full page reload.
5. IF the API_Server returns an error when a user saves an inline edit, THE Frontend SHALL
   display an error message in the table row identifying the failure and restore the previous
   field value.

---

### Requirement 14: Testing Coverage

**User Story:** As a developer, I want automated tests covering the core logic and UI
interactions so that I can refactor confidently as the application evolves.

> **Educational note:** Property-based testing is used for graph traversal logic because the
> correctness of traversal holds as a *general property* — for any valid graph and any node,
> the traversal should find all reachable descendants without duplication or omission. This is
> more thorough than example-based tests because it checks the invariant across many randomly
> generated graphs, not just the handful of examples a developer thought of.

#### Acceptance Criteria

1. THE Pytest suite SHALL include tests for each of the following scenarios:
   a. Direct Dependant identification — a failed node's immediate successors are in the impacted
      set.
   b. Indirect Dependant identification — multi-hop successors are in the impacted set.
   c. Unaffected Component exclusion — nodes with no path from the failed node are NOT in the
      impacted set.
   d. Alternative path exclusion — a Component that has at least one valid Alternative Path (a traversal route that avoids the failed Component and all failed Edges) is NOT included in the impacted set.
   e. Cycle safety — a graph containing a directed cycle does not cause infinite traversal.
   f. Failed-edge handling — an edge marked as failed is excluded from traversal paths.
   g. Unknown-status handling — a Component with "unknown" status propagates uncertainty
      correctly.
   h. Stale evidence warning — a Component with last_observed_at older than the Freshness
      Threshold triggers a staleness warning in the impact report.
   i. Impact Score ranking — a higher-criticality, higher-downstream-count Component receives a
      higher Impact Score than a lower-criticality, lower-downstream-count Component.
   j. Explanation correctness — the generated explanation text for a known two-hop impact path
      matches the expected template output.
   k. Recovery comparison — restoring the Component with the highest downstream count recovers
      more services than restoring a leaf Component.
   l. Invalid edit rejection — submitting a component with a missing required field returns a
      422 response.
   m. Scenario reset — resetting a Scenario restores all Component health statuses to baseline.
   n. Deduplication — a Component reachable via multiple paths appears exactly once in the
      impacted set.
   o. Failed-edge traversal — when a directed Edge is marked as failed (dependency_link_unavailable), that Edge is excluded from traversal; a Component reachable only via that Edge IS included in the impacted set; a Component that has an alternative route not passing through the failed Edge is NOT included.
   p. Data Confidence Score independence — the Impact Score for a given graph and failed Component is identical whether the involved Components have data_quality_score of 0 or 100; only the Data Confidence Score changes.
   q. Simulation endpoint validation — a simulation request with target_type "component" and failure_type "dependency_link_unavailable" returns a 422 error; a request with target_type "edge" and failure_type "component_unavailable" returns a 422 error.
   r. Save as Scenario — after "Save Simulation as Scenario", the new Scenario contains the same Components and Edges as the original baseline; the original Scenario's Components and Edges are unchanged; the new Scenario's Component health statuses reflect the original baseline, not the simulated failure state.
   s. Recovery for edge failure — when the Active Simulation targets an Edge, the Recovery_Planner offers one recovery option (restore the Edge); the projected impact report after edge restoration shows the impacted set without the failed Edge.
2. THE Vitest suite SHALL include tests for each of the following frontend interactions:
   a. Node click — clicking a graph node opens the details panel with correct Component data.
   b. Filter application — applying a type filter hides nodes of other types.
   c. Simulation indicator — activating a simulation displays the "Simulation Active" indicator
      in the top bar.
   d. Reset button — clicking "Reset Simulation" removes the simulation overlay and restores
      baseline node styles.
   e. API error state — when the API_Server returns a 500 error, THE Frontend SHALL display a
      user-facing error message rather than a blank panel.
   f. Scenario switching — when the user selects a different Scenario in the Scenario Picker, the previous simulation overlay is cleared from the display; if the new Scenario has an existing Active Simulation, its overlay is displayed; the previous Scenario's API simulation state is not reset.
3. THE Pytest suite SHALL include the following property-based tests using the Hypothesis library:
   a. DAG equivalence — for any randomly generated directed acyclic graph with no failed Edges and no Alternative Paths that would exclude any node, and any designated failed node, the set of impacted nodes returned by THE Impact_Engine SHALL equal exactly the set returned by NetworkX's nx.descendants(graph, failed_node).
   b. Failed-edge subset — for any valid graph and any designated failed node, removing any single Edge from the graph before running THE Impact_Engine SHALL produce an impacted set that is a subset of (or equal to) the impacted set when that Edge is present. The impacted set SHALL NOT grow as a result of removing an Edge.
   c. Alternative-path monotonicity — for any valid graph, adding a new valid path from a dependency to a Dependant that bypasses the failed Component SHALL result in an impacted set that is a subset of (or equal to) the original impacted set. The impacted set SHALL NOT grow as a result of adding a bypass path.

---

### Requirement 15: Simulation History Page

**User Story:** As an engineer, I want to review past simulations so that I can learn from
previous analyses without re-running them.

#### Acceptance Criteria

1. THE Frontend SHALL display all Simulation_History records on the Simulation History page in
   reverse-chronological order, showing: simulation identifier, failed Component name, failure
   type, timestamp, affected service count, and Impact Score.
2. WHEN a user clicks a Simulation_History record, THE Frontend SHALL display a read-only
   replay of the impact report for that simulation in the details panel.
3. THE API_Server SHALL persist Simulation_History records in the DB. Records survive server restarts and are retained indefinitely in the initial version. No deletion mechanism is provided in the initial version.

---

### Requirement 16: Settings and Data Quality Page

**User Story:** As an engineer, I want a dedicated settings page where I can configure data
quality thresholds and view evidence coverage, so that I can tune how aggressively ImpactLens
warns about incomplete data.

#### Acceptance Criteria

1. THE Settings_Panel SHALL allow a user to view and update the Freshness Threshold (1–8760
   hours), with the change persisted in the DB and taking effect for all subsequent impact
   analyses without requiring a server restart.
2. THE Settings_Panel SHALL display a per-Component evidence coverage table listing each
   Component's name, evidence_source, confirmation_status, data_quality_score, and
   last_observed_at, sortable by each column.
3. THE Settings_Panel SHALL display a data quality distribution chart (using Recharts) showing
   the count of Components in each confirmation_status bucket: confirmed, inferred, unknown.
4. WHEN a user saves a new Freshness Threshold value outside the 1–8760 range, THE Frontend
   SHALL display a validation error and SHALL NOT send the invalid value to the API_Server.
5. IF the API_Server returns an error when the Settings_Panel attempts to save the Freshness
   Threshold, THE Frontend SHALL display an error message identifying the failure and retain
   the previously saved threshold value.

---

## Constraints

The following are firm constraints that apply to the entire ImpactLens system:

- THE Frontend SHALL run on Windows without Docker or a cloud account.
- THE API_Server SHALL run on Windows using a standard Python virtual environment without Docker.
- THE Seed_Loader SHALL populate the DB with data clearly labelled as simulated — no seed data
  SHALL be presented to the user as real infrastructure telemetry.
- THE Impact_Engine SHALL use only deterministic algorithms — given the same graph and the same
  failed Component, repeated simulations SHALL produce identical impact reports.
- THE API_Server SHALL NOT require AWS credentials or any paid external API key to start or
  operate.
- THE Frontend SHALL NOT implement authentication, user login, or role-based access control.
- THE Impact_Engine SHALL NOT use a machine learning model or external AI service to generate
  explanations — all explanations SHALL be produced by template-based text generation.
- THE API_Server SHALL NOT execute any real infrastructure recovery action — all recovery
  analysis is purely simulated projection.
- THE Impact_Engine SHALL report the Impact Score and the Data Confidence Score as two separate values in every impact report. Poor data quality SHALL warn the user but SHALL NOT silently reduce the Impact Score, which always reflects graph topology and criticality alone.
- THE API_Server SHALL allow CORS from http://localhost:5173 by default during development. The allowed origin SHALL be overridable via the CORS_ORIGIN environment variable.
- THE initial version of the Recovery_Planner SHALL support recovery analysis only for the direct simulation target (the failed Component or the failed Edge). Multi-step recovery sequences (restoring multiple Components or Edges in combination) are out of scope for the initial version and SHALL NOT be implemented.
