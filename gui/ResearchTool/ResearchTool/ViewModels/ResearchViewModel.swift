import Foundation
import SwiftUI

/// Research phase states matching backend pipeline
enum ResearchPhase: String, CaseIterable {
    case idle = "idle"
    case starting = "starting"
    case clarify = "clarify"
    case collect = "collect"
    case process = "process"
    case analyze = "analyze"
    case verify = "verify"
    case evaluate = "evaluate"
    case synthesize = "synthesize"
    case export = "export"
    case complete = "complete"

    var displayName: String {
        switch self {
        case .idle: return "Idle"
        case .starting: return "Starting"
        case .clarify: return "Clarifying"
        case .collect: return "Collecting"
        case .process: return "Processing"
        case .analyze: return "Analyzing"
        case .verify: return "Verifying"
        case .evaluate: return "Evaluating"
        case .synthesize: return "Synthesizing"
        case .export: return "Exporting"
        case .complete: return "Complete"
        }
    }

    var icon: String {
        switch self {
        case .idle: return "circle"
        case .starting: return "play.circle"
        case .clarify: return "magnifyingglass"
        case .collect: return "arrow.down.doc"
        case .process: return "gearshape"
        case .analyze: return "chart.bar"
        case .verify: return "checkmark.shield"
        case .evaluate: return "star"
        case .synthesize: return "doc.text"
        case .export: return "square.and.arrow.up"
        case .complete: return "checkmark.circle.fill"
        }
    }

    var stepNumber: Int {
        switch self {
        case .idle: return 0
        case .starting: return 1
        case .clarify: return 2
        case .collect: return 3
        case .process: return 4
        case .analyze: return 5
        case .verify: return 6
        case .evaluate: return 7
        case .synthesize: return 8
        case .export: return 9
        case .complete: return 10
        }
    }
}

/// ViewModel managing research session state and API communication
@MainActor
class ResearchViewModel: ObservableObject {

    // MARK: - Published Properties

    @Published var query: String = ""
    @Published var isResearching: Bool = false
    @Published var currentPhase: ResearchPhase = .idle
    @Published var progress: Double = 0.0 // 0-1
    @Published var entitiesCount: Int = 0
    @Published var factsCount: Int = 0
    @Published var sourcesCount: Int = 0
    @Published var saturationPercent: Double = 0.0
    @Published var errorMessage: String?
    @Published var sessionId: String?
    @Published var privacyMode: PrivacyMode = .cloudAllowed
    @Published var showingExport: Bool = false

    // MARK: - Private Properties

    private var pollingTask: Task<Void, Never>?

    // MARK: - Public Methods

    /// Start a new research session
    func startResearch(query: String) async {
        guard !query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return
        }

        // Reset state
        errorMessage = nil
        currentPhase = .starting
        progress = 0.0
        entitiesCount = 0
        factsCount = 0
        sourcesCount = 0
        saturationPercent = 0.0

        isResearching = true

        do {
            // Use APIClient instead of manual URL construction
            let response = try await APIClient.shared.startResearch(
                query: query,
                privacyMode: privacyMode.rawValue.lowercased()
            )

            sessionId = response.sessionId
            AppState.shared.startResearchSession(id: response.sessionId)

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
            // Use APIClient
            _ = try await APIClient.shared.stopResearch(sessionId: id)
        } catch {
            handleError(error)
        }

        isResearching = false
        currentPhase = .complete
        AppState.shared.endResearchSession()
    }

    /// Reset the research state
    func reset() {
        pollingTask?.cancel()
        pollingTask = nil

        query = ""
        isResearching = false
        currentPhase = .idle
        progress = 0.0
        entitiesCount = 0
        factsCount = 0
        sourcesCount = 0
        saturationPercent = 0.0
        errorMessage = nil
        sessionId = nil
        showingExport = false

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
            // Use APIClient for status polling
            let status = try await APIClient.shared.getResearchStatus(sessionId: id)

            // Update phase
            if let phase = ResearchPhase(rawValue: status.currentPhase.lowercased()) {
                currentPhase = phase
                // Calculate progress based on phase
                progress = Double(phase.stepNumber) / Double(ResearchPhase.allCases.count - 1)
            }

            // Update stats - these are arrays, get their counts
            entitiesCount = status.entitiesFound.count
            factsCount = status.factsExtracted.count
            sourcesCount = status.sourcesQueried.count

            // Update saturation from metrics
            if let metrics = status.saturationMetrics,
               let saturation = metrics.overallSaturation {
                saturationPercent = saturation * 100.0
            }

            // Check if research should stop
            if status.shouldStop {
                pollingTask?.cancel()
                pollingTask = nil
                isResearching = false
                currentPhase = .complete
                AppState.shared.endResearchSession()
            }

        } catch {
            // Don't stop polling on transient errors, just log
            print("[ResearchViewModel] Poll error: \(error.localizedDescription)")
            // Only show error if it's not a transient network issue
            if !(error is URLError) && !(error is APIError) {
                handleError(error)
            }
        }
    }

    private func handleError(_ error: Error) {
        if let researchError = error as? ResearchError {
            errorMessage = researchError.localizedDescription
        } else {
            errorMessage = error.localizedDescription
        }
    }
}

// MARK: - Research Errors

enum ResearchError: LocalizedError {
    case invalidURL
    case invalidResponse
    case httpError(Int)
    case serverError(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL"
        case .invalidResponse:
            return "Invalid server response"
        case .httpError(let code):
            return "Server error (HTTP \(code))"
        case .serverError(let message):
            return message
        }
    }
}
