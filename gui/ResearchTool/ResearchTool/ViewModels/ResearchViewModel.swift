import Foundation
import SwiftUI

/// Research phase states matching backend pipeline
enum ResearchPhase: String, CaseIterable {
    case idle = "idle"
    case starting = "starting"
    case clarify = "clarify"
    case plan = "plan"
    case collect = "collect"
    case process = "process"
    case analyze = "analyze"
    case verify = "verify"
    case evaluate = "evaluate"
    case synthesize = "synthesize"
    case export = "export"
    case complete = "complete"
    case failed = "failed"
    case awaitingApproval = "awaiting_approval"

    var displayName: String {
        switch self {
        case .idle: return "Idle"
        case .starting: return "Starting"
        case .clarify: return "Clarifying"
        case .plan: return "Planning"
        case .collect: return "Collecting"
        case .process: return "Processing"
        case .analyze: return "Analyzing"
        case .verify: return "Verifying"
        case .evaluate: return "Evaluating"
        case .synthesize: return "Synthesizing"
        case .export: return "Exporting"
        case .complete: return "Complete"
        case .failed: return "Failed"
        case .awaitingApproval: return "Awaiting Approval"
        }
    }

    var icon: String {
        switch self {
        case .idle: return "circle"
        case .starting: return "play.circle"
        case .clarify: return "questionmark.circle"
        case .plan: return "list.bullet.clipboard"
        case .collect: return "arrow.down.doc"
        case .process: return "gearshape"
        case .analyze: return "chart.bar"
        case .verify: return "checkmark.shield"
        case .evaluate: return "star"
        case .synthesize: return "doc.text"
        case .export: return "square.and.arrow.up"
        case .complete: return "checkmark.circle.fill"
        case .failed: return "xmark.circle.fill"
        case .awaitingApproval: return "hand.raised"
        }
    }

    var stepNumber: Int {
        switch self {
        case .idle: return 0
        case .starting: return 1
        case .clarify: return 2
        case .plan: return 3
        case .collect: return 4
        case .process: return 5
        case .analyze: return 6
        case .verify: return 7
        case .evaluate: return 8
        case .synthesize: return 9
        case .export: return 10
        case .complete: return 11
        case .failed: return 11
        case .awaitingApproval: return 3  // Same as plan (waiting for user)
        }
    }

    /// Phases to show in the progress indicator (excludes idle, complete, failed, awaitingApproval)
    static var progressPhases: [ResearchPhase] {
        [.starting, .clarify, .plan, .collect, .process, .analyze, .verify, .evaluate, .synthesize, .export]
    }
}

/// Research status from backend
enum ResearchStatus: String {
    case running = "running"
    case completed = "completed"
    case failed = "failed"

    var isTerminal: Bool {
        self == .completed || self == .failed
    }
}

/// ViewModel managing research session state and API communication
@MainActor
class ResearchViewModel: ObservableObject {

    // MARK: - Published Properties

    @Published var query: String = ""
    @Published var isResearching: Bool = false
    @Published var currentPhase: ResearchPhase = .idle
    @Published var researchStatus: ResearchStatus = .running
    @Published var progress: Double = 0.0 // 0-1
    @Published var entitiesCount: Int = 0
    @Published var factsCount: Int = 0
    @Published var sourcesCount: Int = 0
    @Published var saturationPercent: Double = 0.0
    @Published var errorMessage: String?
    @Published var sessionId: String?
    @Published var privacyMode: PrivacyMode = .cloudAllowed
    @Published var showingExport: Bool = false
    @Published var stopReason: String?

    /// The final report when research completes
    @Published var finalReport: ResearchReportResponse?

    /// Whether research is waiting for user approval to continue
    @Published var isAwaitingApproval: Bool = false

    // MARK: - Private Properties

    private var pollingTask: Task<Void, Never>?

    // MARK: - Computed Properties

    /// Whether the research has completed (successfully or with failure)
    var isComplete: Bool {
        currentPhase == .complete || currentPhase == .failed
    }

    /// Whether the research failed
    var isFailed: Bool {
        currentPhase == .failed || researchStatus == .failed
    }

    /// Whether export is available (research completed successfully)
    var canExport: Bool {
        currentPhase == .complete && finalReport != nil
    }

    // MARK: - Public Methods

    /// Start a new research session
    func startResearch(query: String) async {
        guard !query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return
        }

        // Reset state
        errorMessage = nil
        currentPhase = .starting
        researchStatus = .running
        progress = 0.0
        entitiesCount = 0
        factsCount = 0
        sourcesCount = 0
        saturationPercent = 0.0
        stopReason = nil
        finalReport = nil
        isAwaitingApproval = false

        isResearching = true

        do {
            let response = try await APIClient.shared.startResearch(
                query: query,
                privacyMode: privacyMode.rawValue.lowercased()
            )

            sessionId = response.sessionId
            AppState.shared.startResearchSession(id: response.sessionId)

            print("[ResearchViewModel] Started session: \(response.sessionId)")

            // Start polling status
            startPolling()

        } catch {
            handleError(error)
            isResearching = false
        }
    }

    /// Stop the current research session
    func stopResearch() async {
        guard let id = sessionId else { return }

        // Cancel polling
        pollingTask?.cancel()
        pollingTask = nil

        do {
            let response = try await APIClient.shared.stopResearch(sessionId: id)
            print("[ResearchViewModel] Stop response: \(response.status)")
        } catch {
            handleError(error)
        }

        isResearching = false
        currentPhase = .complete
        stopReason = "User requested stop"
        AppState.shared.endResearchSession()
    }

    /// Approve research plan to continue workflow
    func approveResearchPlan() async {
        guard let id = sessionId else { return }

        do {
            let response = try await APIClient.shared.approveResearchPlan(sessionId: id)
            print("[ResearchViewModel] Approve response: \(response.status)")
            isAwaitingApproval = false
        } catch {
            handleError(error)
        }
    }

    /// Fetch the final report for a completed session
    func fetchReport() async {
        guard let id = sessionId else { return }

        do {
            finalReport = try await APIClient.shared.getResearchReport(sessionId: id)
            print("[ResearchViewModel] Fetched report with \(finalReport?.facts?.count ?? 0) facts")

            // Auto-save to library
            await saveToLibrary()
        } catch {
            handleError(error)
        }
    }

    /// Save completed research to library for future reference
    private func saveToLibrary() async {
        guard let id = sessionId, let report = finalReport else { return }

        // Convert AnyCodableValue facts to [String: Any]
        let factsData: [[String: Any]] = report.facts?.map { dict in
            var result: [String: Any] = [:]
            for (key, value) in dict {
                switch value {
                case .string(let s): result[key] = s
                case .int(let i): result[key] = i
                case .double(let d): result[key] = d
                case .bool(let b): result[key] = b
                default: break
                }
            }
            return result
        } ?? []

        // Convert AnyCodableValue sources to [String: Any]
        let sourcesData: [[String: Any]] = report.sources?.map { dict in
            var result: [String: Any] = [:]
            for (key, value) in dict {
                switch value {
                case .string(let s): result[key] = s
                case .int(let i): result[key] = i
                case .double(let d): result[key] = d
                case .bool(let b): result[key] = b
                default: break
                }
            }
            return result
        } ?? []

        do {
            _ = try await APIClient.shared.saveToLibrary(
                sessionId: id,
                query: query,
                domain: report.domain ?? "general",
                privacyMode: privacyMode.rawValue.lowercased(),
                status: "completed",
                summary: report.summary,
                facts: factsData,
                sources: sourcesData,
                entities: report.entities ?? [],
                confidenceScore: report.confidenceScore,
                startedAt: nil,  // TODO: Track started_at properly
                completedAt: Date()
            )
            print("[ResearchViewModel] Session saved to library: \(id)")
        } catch {
            // Don't fail the research if library save fails
            print("[ResearchViewModel] Failed to save to library: \(error.localizedDescription)")
        }
    }

    /// Reset the research state
    func reset() {
        pollingTask?.cancel()
        pollingTask = nil

        query = ""
        isResearching = false
        currentPhase = .idle
        researchStatus = .running
        progress = 0.0
        entitiesCount = 0
        factsCount = 0
        sourcesCount = 0
        saturationPercent = 0.0
        errorMessage = nil
        sessionId = nil
        showingExport = false
        stopReason = nil
        finalReport = nil
        isAwaitingApproval = false

        AppState.shared.endResearchSession()
    }

    // MARK: - Private Methods

    private func startPolling() {
        pollingTask = Task {
            while !Task.isCancelled && isResearching {
                await pollStatus()

                // Poll every 2 seconds
                try? await Task.sleep(nanoseconds: 2_000_000_000)
            }
        }
    }

    private func pollStatus() async {
        guard let id = sessionId else { return }

        do {
            let status = try await APIClient.shared.getResearchStatus(sessionId: id)

            // Update research status
            if let rs = ResearchStatus(rawValue: status.status) {
                researchStatus = rs
            }

            // Update phase from current_phase string
            if let phaseString = status.currentPhase?.lowercased(),
               let phase = ResearchPhase(rawValue: phaseString) {
                currentPhase = phase
                // Calculate progress based on phase
                let totalPhases = Double(ResearchPhase.progressPhases.count)
                progress = min(Double(phase.stepNumber) / totalPhases, 1.0)
            }

            // Update stats - these are integers from the backend
            entitiesCount = status.entitiesFound
            factsCount = status.factsExtracted
            sourcesCount = status.sourcesQueried

            // Update saturation from metrics
            if let metrics = status.saturationMetrics {
                saturationPercent = metrics.overallSaturation
            }

            // Store stop reason if present
            if let reason = status.stopReason {
                stopReason = reason
            }

            // Check if research is complete based on status field
            if status.isComplete {
                pollingTask?.cancel()
                pollingTask = nil
                isResearching = false

                if status.isFailed {
                    currentPhase = .failed
                    errorMessage = status.stopReason ?? "Research failed"
                } else {
                    currentPhase = .complete
                    // Fetch the final report
                    await fetchReport()
                }

                AppState.shared.endResearchSession()
            }

        } catch {
            // Log error but don't stop polling for transient errors
            print("[ResearchViewModel] Poll error: \(error.localizedDescription)")

            // Only show error to user for persistent issues
            if let apiError = error as? APIError {
                switch apiError {
                case .httpError(404):
                    // Session not found - stop polling
                    pollingTask?.cancel()
                    pollingTask = nil
                    isResearching = false
                    currentPhase = .failed
                    errorMessage = "Research session not found"
                    AppState.shared.endResearchSession()
                case .serverError(let msg):
                    errorMessage = msg
                default:
                    // Transient error - continue polling
                    break
                }
            }
        }
    }

    private func handleError(_ error: Error) {
        if let apiError = error as? APIError {
            errorMessage = apiError.localizedDescription
        } else {
            errorMessage = error.localizedDescription
        }
        print("[ResearchViewModel] Error: \(errorMessage ?? "unknown")")
    }
}
