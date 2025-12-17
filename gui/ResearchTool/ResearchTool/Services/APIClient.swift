import Foundation

/// API errors that can occur during network requests
enum APIError: LocalizedError {
    case invalidURL
    case networkError(Error)
    case httpError(Int)
    case decodingError(Error)
    case serverError(String)
    case invalidResponse

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .httpError(let code):
            return "HTTP error: \(code)"
        case .decodingError(let error):
            return "Failed to decode response: \(error.localizedDescription)"
        case .serverError(let message):
            return message
        case .invalidResponse:
            return "Invalid server response"
        }
    }
}

// MARK: - Response Models (Matching Backend OpenAPI Spec)

/// Response from POST /api/research/start
struct StartResearchResponse: Codable {
    let sessionId: String
    let status: String
    let message: String?

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case status
        case message
    }
}

/// Response from GET /api/research/{session_id}/status
/// Matches backend ResearchStatus schema exactly
struct ResearchStatusResponse: Codable {
    let sessionId: String
    let status: String  // "running", "completed", "failed"
    let currentPhase: String?
    let sourcesQueried: Int
    let entitiesFound: Int
    let factsExtracted: Int
    let saturationMetrics: SaturationMetrics?
    let stopReason: String?
    let exportPath: String?

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case status
        case currentPhase = "current_phase"
        case sourcesQueried = "sources_queried"
        case entitiesFound = "entities_found"
        case factsExtracted = "facts_extracted"
        case saturationMetrics = "saturation_metrics"
        case stopReason = "stop_reason"
        case exportPath = "export_path"
    }

    /// Convenience: Check if research is complete
    var isComplete: Bool {
        status == "completed" || status == "failed"
    }

    /// Convenience: Check if research failed
    var isFailed: Bool {
        status == "failed"
    }
}

/// Saturation metrics from backend evaluate.py
/// Keys match backend: new_entities_ratio, new_facts_ratio, citation_circularity, source_coverage
struct SaturationMetrics: Codable {
    let newEntitiesRatio: Double?
    let newFactsRatio: Double?
    let citationCircularity: Double?
    let sourceCoverage: Double?

    enum CodingKeys: String, CodingKey {
        case newEntitiesRatio = "new_entities_ratio"
        case newFactsRatio = "new_facts_ratio"
        case citationCircularity = "citation_circularity"
        case sourceCoverage = "source_coverage"
    }

    /// Calculate overall saturation (0-100%)
    var overallSaturation: Double {
        let entitySat = 1.0 - min(newEntitiesRatio ?? 1.0, 1.0)
        let factSat = 1.0 - min(newFactsRatio ?? 1.0, 1.0)
        let coverage = sourceCoverage ?? 0.0
        return (0.4 * entitySat + 0.4 * factSat + 0.2 * coverage) * 100.0
    }
}

/// Response from POST /api/research/{session_id}/stop
struct StopResearchResponse: Codable {
    let sessionId: String
    let status: String
    let message: String?

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case status
        case message
    }
}

/// Response from POST /api/research/{session_id}/approve
struct ApproveResearchResponse: Codable {
    let sessionId: String
    let status: String
    let message: String?

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case status
        case message
    }
}

/// Response from GET /api/research/{session_id}/report
struct ResearchReportResponse: Codable {
    let sessionId: String?
    let query: String?
    let domain: String?
    let summary: String?
    let facts: [[String: AnyCodableValue]]?
    let sources: [[String: AnyCodableValue]]?
    let entities: [String]?
    let confidenceScore: Double?
    let limitations: [String]?
    let generatedAt: String?

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case query
        case domain
        case summary
        case facts
        case sources
        case entities
        case confidenceScore = "confidence_score"
        case limitations
        case generatedAt = "generated_at"
    }
}

/// Session summary for list endpoint
struct ResearchSessionSummary: Codable {
    let sessionId: String
    let status: String
    let query: String
    let currentPhase: String?
    let startedAt: String?

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case status
        case query
        case currentPhase = "current_phase"
        case startedAt = "started_at"
    }
}

/// Response from GET /api/export/formats - array of ExportFormatInfo
struct ExportFormatInfo: Codable {
    let format: String
    let mimeType: String
    let fileExtension: String
    let description: String

    enum CodingKeys: String, CodingKey {
        case format
        case mimeType = "mime_type"
        case fileExtension = "file_extension"
        case description
    }
}

/// Response from GET /api/health
struct HealthResponse: Codable {
    let status: String
    let version: String?
}

// MARK: - Library Response Models

/// Response from GET /api/library/sessions
struct LibrarySessionListResponse: Codable {
    let sessions: [LibrarySessionSummary]
    let total: Int
    let offset: Int
    let limit: Int
}

/// Summary of a session in the library
struct LibrarySessionSummary: Codable, Identifiable {
    let sessionId: String
    let query: String
    let domain: String
    let status: String
    let factsCount: Int
    let sourcesCount: Int
    let confidenceScore: Double?
    let startedAt: String?
    let completedAt: String?

    var id: String { sessionId }

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case query
        case domain
        case status
        case factsCount = "facts_count"
        case sourcesCount = "sources_count"
        case confidenceScore = "confidence_score"
        case startedAt = "started_at"
        case completedAt = "completed_at"
    }

    /// Format started_at as readable date
    var formattedDate: String {
        guard let dateString = startedAt else { return "Unknown" }
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = formatter.date(from: dateString) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateStyle = .medium
            displayFormatter.timeStyle = .short
            return displayFormatter.string(from: date)
        }
        return dateString
    }
}

/// Full session detail from GET /api/library/sessions/{id}
struct LibrarySessionDetail: Codable {
    let sessionId: String
    let query: String
    let domain: String
    let privacyMode: String
    let status: String
    let summary: String?
    let facts: [[String: AnyCodableValue]]
    let sources: [[String: AnyCodableValue]]
    let entities: [String]
    let confidenceScore: Double?
    let startedAt: String
    let completedAt: String?
    let saturationMetrics: [String: AnyCodableValue]?

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case query
        case domain
        case privacyMode = "privacy_mode"
        case status
        case summary
        case facts
        case sources
        case entities
        case confidenceScore = "confidence_score"
        case startedAt = "started_at"
        case completedAt = "completed_at"
        case saturationMetrics = "saturation_metrics"
    }
}

/// Search result from GET /api/library/search
struct LibrarySearchResult: Codable, Identifiable {
    let sessionId: String
    let query: String
    let summary: String?
    let startedAt: String
    let rank: Double

    var id: String { sessionId }

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case query
        case summary
        case startedAt = "started_at"
        case rank
    }
}

/// Response from GET /api/library/search
struct LibrarySearchResponse: Codable {
    let results: [LibrarySearchResult]
    let query: String
    let total: Int
}

/// Response from GET /api/library/stats
struct LibraryStatsResponse: Codable {
    let totalSessions: Int
    let totalFacts: Int
    let totalSources: Int
    let completedSessions: Int
    let averageConfidence: Double?

    enum CodingKeys: String, CodingKey {
        case totalSessions = "total_sessions"
        case totalFacts = "total_facts"
        case totalSources = "total_sources"
        case completedSessions = "completed_sessions"
        case averageConfidence = "average_confidence"
    }
}

/// Response from GET /api/health/detailed
struct DetailedHealthResponse: Codable {
    let status: String
    let components: [String: ComponentHealth]?
    let providersAvailable: Int?

    enum CodingKeys: String, CodingKey {
        case status
        case components
        case providersAvailable = "providers_available"
    }
}

struct ComponentHealth: Codable {
    let status: String?
    let configured: Bool?
    let healthy: Bool?
    let models: [String]?
    let error: String?
}

// MARK: - Helper for decoding mixed JSON values

enum AnyCodableValue: Codable {
    case string(String)
    case int(Int)
    case double(Double)
    case bool(Bool)
    case array([AnyCodableValue])
    case dictionary([String: AnyCodableValue])
    case null

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()

        if container.decodeNil() {
            self = .null
            return
        }

        if let bool = try? container.decode(Bool.self) {
            self = .bool(bool)
            return
        }

        if let int = try? container.decode(Int.self) {
            self = .int(int)
            return
        }

        if let double = try? container.decode(Double.self) {
            self = .double(double)
            return
        }

        if let string = try? container.decode(String.self) {
            self = .string(string)
            return
        }

        if let array = try? container.decode([AnyCodableValue].self) {
            self = .array(array)
            return
        }

        if let dict = try? container.decode([String: AnyCodableValue].self) {
            self = .dictionary(dict)
            return
        }

        throw DecodingError.typeMismatch(
            AnyCodableValue.self,
            DecodingError.Context(codingPath: decoder.codingPath, debugDescription: "Unsupported type")
        )
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let value): try container.encode(value)
        case .int(let value): try container.encode(value)
        case .double(let value): try container.encode(value)
        case .bool(let value): try container.encode(value)
        case .array(let value): try container.encode(value)
        case .dictionary(let value): try container.encode(value)
        case .null: try container.encodeNil()
        }
    }

    var stringValue: String? {
        if case .string(let s) = self { return s }
        return nil
    }

    var doubleValue: Double? {
        switch self {
        case .double(let d): return d
        case .int(let i): return Double(i)
        default: return nil
        }
    }
}

// MARK: - API Client

/// Centralized HTTP client for all backend API calls
@MainActor
class APIClient {

    // MARK: - Singleton

    static let shared = APIClient()

    // MARK: - Properties

    private let baseURL: String
    private let defaultTimeout: TimeInterval = 30
    private let researchTimeout: TimeInterval = 120

    // MARK: - Initialization

    private init(baseURL: String = "http://localhost:8000") {
        self.baseURL = baseURL
    }

    // MARK: - Research Endpoints

    /// List all active research sessions
    /// GET /api/research
    func listSessions() async throws -> [ResearchSessionSummary] {
        return try await get(path: "/api/research", timeout: defaultTimeout)
    }

    /// Start a new research session
    /// POST /api/research/start
    func startResearch(query: String, privacyMode: String, domain: String? = nil, maxSources: Int = 20) async throws -> StartResearchResponse {
        var body: [String: Any] = [
            "query": query,
            "privacy_mode": privacyMode,
            "max_sources": maxSources
        ]
        if let domain = domain {
            body["domain"] = domain
        }
        return try await post(
            path: "/api/research/start",
            body: body,
            timeout: researchTimeout
        )
    }

    /// Get status of a research session
    /// GET /api/research/{session_id}/status
    func getResearchStatus(sessionId: String) async throws -> ResearchStatusResponse {
        return try await get(
            path: "/api/research/\(sessionId)/status",
            timeout: defaultTimeout
        )
    }

    /// Stop a research session
    /// POST /api/research/{session_id}/stop
    func stopResearch(sessionId: String) async throws -> StopResearchResponse {
        return try await post(
            path: "/api/research/\(sessionId)/stop",
            body: [:],
            timeout: defaultTimeout
        )
    }

    /// Approve research plan to continue workflow
    /// POST /api/research/{session_id}/approve
    func approveResearchPlan(sessionId: String) async throws -> ApproveResearchResponse {
        return try await post(
            path: "/api/research/\(sessionId)/approve",
            body: [:],
            timeout: defaultTimeout
        )
    }

    /// Get final research report
    /// GET /api/research/{session_id}/report
    func getResearchReport(sessionId: String) async throws -> ResearchReportResponse {
        return try await get(
            path: "/api/research/\(sessionId)/report",
            timeout: researchTimeout
        )
    }

    // MARK: - Export Endpoints

    /// Get available export formats
    /// GET /api/export/formats
    func getExportFormats() async throws -> [ExportFormatInfo] {
        return try await get(path: "/api/export/formats", timeout: defaultTimeout)
    }

    /// Export research results
    /// POST /api/export
    /// Note: Backend expects the full report data, not just session_id
    func exportResearch(report: ResearchReportResponse, format: String) async throws -> Data {
        let body: [String: Any] = [
            "format": format,
            "query": report.query ?? "",
            "domain": report.domain ?? "general",
            "summary": report.summary ?? "",
            "facts": report.facts?.map { dict -> [String: Any] in
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
            } ?? [],
            "sources": report.sources?.map { dict -> [String: Any] in
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
            } ?? [],
            "confidence_score": report.confidenceScore ?? 0.0,
            "limitations": report.limitations ?? []
        ]
        return try await postRaw(path: "/api/export", body: body)
    }

    // MARK: - Health Endpoints

    /// Basic health check
    /// GET /api/health
    func checkHealth() async throws -> HealthResponse {
        return try await get(path: "/api/health", timeout: 5)
    }

    /// Detailed health check with component status
    /// GET /api/health/detailed
    func checkDetailedHealth() async throws -> DetailedHealthResponse {
        return try await get(path: "/api/health/detailed", timeout: 10)
    }

    // MARK: - Library Endpoints

    /// List all sessions in the library with pagination
    /// GET /api/library/sessions
    func listLibrarySessions(offset: Int = 0, limit: Int = 20) async throws -> LibrarySessionListResponse {
        return try await get(
            path: "/api/library/sessions?offset=\(offset)&limit=\(limit)",
            timeout: defaultTimeout
        )
    }

    /// Get full details of a library session
    /// GET /api/library/sessions/{id}
    func getLibrarySession(sessionId: String) async throws -> LibrarySessionDetail {
        return try await get(
            path: "/api/library/sessions/\(sessionId)",
            timeout: defaultTimeout
        )
    }

    /// Delete a session from the library
    /// DELETE /api/library/sessions/{id}
    func deleteLibrarySession(sessionId: String) async throws -> [String: String] {
        return try await delete(
            path: "/api/library/sessions/\(sessionId)",
            timeout: defaultTimeout
        )
    }

    /// Search library using full-text search
    /// GET /api/library/search
    func searchLibrary(query: String, limit: Int = 20) async throws -> LibrarySearchResponse {
        let encodedQuery = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query
        return try await get(
            path: "/api/library/search?q=\(encodedQuery)&limit=\(limit)",
            timeout: defaultTimeout
        )
    }

    /// Get library statistics
    /// GET /api/library/stats
    func getLibraryStats() async throws -> LibraryStatsResponse {
        return try await get(path: "/api/library/stats", timeout: defaultTimeout)
    }

    /// Save a completed research session to the library
    /// POST /api/library/sessions
    func saveToLibrary(
        sessionId: String,
        query: String,
        domain: String,
        privacyMode: String,
        status: String,
        summary: String?,
        facts: [[String: Any]],
        sources: [[String: Any]],
        entities: [String],
        confidenceScore: Double?,
        startedAt: Date?,
        completedAt: Date?
    ) async throws -> [String: String] {
        let dateFormatter = ISO8601DateFormatter()
        dateFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

        var body: [String: Any] = [
            "session_id": sessionId,
            "query": query,
            "domain": domain,
            "privacy_mode": privacyMode,
            "status": status,
            "facts": facts,
            "sources": sources,
            "entities": entities
        ]

        if let summary = summary {
            body["summary"] = summary
        }
        if let confidence = confidenceScore {
            body["confidence_score"] = confidence
        }
        if let started = startedAt {
            body["started_at"] = dateFormatter.string(from: started)
        }
        if let completed = completedAt {
            body["completed_at"] = dateFormatter.string(from: completed)
        }

        return try await post(path: "/api/library/sessions", body: body, timeout: defaultTimeout)
    }

    // MARK: - Generic Request Helpers

    private func get<T: Decodable>(path: String, timeout: TimeInterval) async throws -> T {
        guard let url = URL(string: "\(baseURL)\(path)") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = timeout

        return try await execute(request)
    }

    private func post<T: Decodable>(
        path: String,
        body: [String: Any],
        timeout: TimeInterval
    ) async throws -> T {
        guard let url = URL(string: "\(baseURL)\(path)") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = timeout
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        return try await execute(request)
    }

    private func delete<T: Decodable>(path: String, timeout: TimeInterval) async throws -> T {
        guard let url = URL(string: "\(baseURL)\(path)") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        request.timeoutInterval = timeout

        return try await execute(request)
    }

    private func postRaw(path: String, body: [String: Any]) async throws -> Data {
        guard let url = URL(string: "\(baseURL)\(path)") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = researchTimeout
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        do {
            let (data, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }

            guard (200...299).contains(httpResponse.statusCode) else {
                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let detail = json["detail"] as? String {
                    throw APIError.serverError(detail)
                }
                throw APIError.httpError(httpResponse.statusCode)
            }

            return data
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.networkError(error)
        }
    }

    private func execute<T: Decodable>(_ request: URLRequest) async throws -> T {
        do {
            let (data, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }

            guard (200...299).contains(httpResponse.statusCode) else {
                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let detail = json["detail"] as? String {
                    throw APIError.serverError(detail)
                }
                throw APIError.httpError(httpResponse.statusCode)
            }

            let decoder = JSONDecoder()
            return try decoder.decode(T.self, from: data)

        } catch let error as APIError {
            throw error
        } catch let error as DecodingError {
            print("[APIClient] Decoding error: \(error)")
            throw APIError.decodingError(error)
        } catch {
            throw APIError.networkError(error)
        }
    }
}
