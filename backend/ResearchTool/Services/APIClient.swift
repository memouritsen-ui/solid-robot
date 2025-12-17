//
//  APIClient.swift
//  ResearchTool
//
//  Created on 2025-12-17.
//

import Foundation

// MARK: - API Error

enum APIError: Error, LocalizedError {
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
        case .httpError(let statusCode):
            return "HTTP error: \(statusCode)"
        case .decodingError(let error):
            return "Failed to decode response: \(error.localizedDescription)"
        case .serverError(let message):
            return "Server error: \(message)"
        case .invalidResponse:
            return "Invalid response from server"
        }
    }
}

// MARK: - Response Models

struct StartResearchResponse: Codable {
    let sessionId: String
    let status: String

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case status
    }
}

struct ResearchStatusResponse: Codable {
    let sessionId: String
    let status: String
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

    struct SaturationMetrics: Codable {
        let newEntitiesRatio: Double
        let newFactsRatio: Double
        let citationCircularity: Double
        let sourceCoverage: Double

        enum CodingKeys: String, CodingKey {
            case newEntitiesRatio = "new_entities_ratio"
            case newFactsRatio = "new_facts_ratio"
            case citationCircularity = "citation_circularity"
            case sourceCoverage = "source_coverage"
        }
    }
}

struct StopResearchResponse: Codable {
    let status: String
}

struct ResearchReportResponse: Codable {
    let sessionId: String
    let finalReport: FinalReport

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case finalReport = "final_report"
    }

    struct FinalReport: Codable {
        let summary: String
        let entities: [String]
        let facts: [String]
        let sources: [String]
        let generatedAt: String?

        enum CodingKeys: String, CodingKey {
            case summary
            case entities
            case facts
            case sources
            case generatedAt = "generated_at"
        }
    }
}

struct ExportFormatsResponse: Codable {
    let formats: [String]
}

struct HealthResponse: Codable {
    let status: String
}

// MARK: - Request Models

struct StartResearchRequest: Codable {
    let query: String
    let privacyMode: String

    enum CodingKeys: String, CodingKey {
        case query
        case privacyMode = "privacy_mode"
    }
}

struct ExportRequest: Codable {
    let sessionId: String
    let format: String
    let options: [String: AnyCodable]

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case format
        case options
    }
}

// MARK: - AnyCodable Helper

struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()

        if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let string = try? container.decode(String.self) {
            value = string
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array.map { $0.value }
        } else if let dictionary = try? container.decode([String: AnyCodable].self) {
            value = dictionary.mapValues { $0.value }
        } else {
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Unsupported type")
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()

        switch value {
        case let bool as Bool:
            try container.encode(bool)
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let string as String:
            try container.encode(string)
        case let array as [Any]:
            try container.encode(array.map { AnyCodable($0) })
        case let dictionary as [String: Any]:
            try container.encode(dictionary.mapValues { AnyCodable($0) })
        default:
            throw EncodingError.invalidValue(value, EncodingError.Context(codingPath: [], debugDescription: "Unsupported type"))
        }
    }
}

// MARK: - API Client

class APIClient {

    // MARK: - Singleton

    static let shared = APIClient()

    // MARK: - Properties

    var baseURL: String = "http://localhost:8000"

    private let session: URLSession
    private let defaultTimeout: TimeInterval = 30.0
    private let researchOperationTimeout: TimeInterval = 120.0

    // MARK: - Initialization

    private init() {
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = defaultTimeout
        configuration.timeoutIntervalForResource = defaultTimeout
        self.session = URLSession(configuration: configuration)
    }

    // MARK: - Generic Request Helper

    private func request<T: Decodable>(
        endpoint: String,
        method: String = "GET",
        body: Data? = nil,
        timeout: TimeInterval? = nil
    ) async throws -> T {
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.timeoutInterval = timeout ?? defaultTimeout

        if let body = body {
            request.httpBody = body
        }

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            // Try to decode error message from server
            if let errorResponse = try? JSONDecoder().decode([String: String].self, from: data),
               let errorMessage = errorResponse["error"] ?? errorResponse["detail"] {
                throw APIError.serverError(errorMessage)
            }
            throw APIError.httpError(httpResponse.statusCode)
        }

        do {
            let decoder = JSONDecoder()
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }

    private func requestData(
        endpoint: String,
        method: String = "GET",
        body: Data? = nil,
        timeout: TimeInterval? = nil
    ) async throws -> Data {
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = timeout ?? defaultTimeout

        if let body = body {
            request.httpBody = body
        }

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            // Try to decode error message from server
            if let errorResponse = try? JSONDecoder().decode([String: String].self, from: data),
               let errorMessage = errorResponse["error"] ?? errorResponse["detail"] {
                throw APIError.serverError(errorMessage)
            }
            throw APIError.httpError(httpResponse.statusCode)
        }

        return data
    }

    // MARK: - API Endpoints

    /// Start a new research session
    /// - Parameters:
    ///   - query: Research query string
    ///   - privacyMode: "LOCAL_ONLY" or "CLOUD_ALLOWED"
    /// - Returns: StartResearchResponse with session_id and status
    func startResearch(query: String, privacyMode: String) async throws -> StartResearchResponse {
        let requestBody = StartResearchRequest(query: query, privacyMode: privacyMode)
        let encoder = JSONEncoder()
        let bodyData = try encoder.encode(requestBody)

        return try await request(
            endpoint: "/api/research/start",
            method: "POST",
            body: bodyData,
            timeout: researchOperationTimeout
        )
    }

    /// Get the current status of a research session
    /// - Parameter sessionId: The session ID
    /// - Returns: ResearchStatusResponse with current phase, entities, facts, etc.
    func getResearchStatus(sessionId: String) async throws -> ResearchStatusResponse {
        return try await request(
            endpoint: "/api/research/\(sessionId)/status",
            method: "GET",
            timeout: defaultTimeout
        )
    }

    /// Stop an active research session
    /// - Parameter sessionId: The session ID
    /// - Returns: StopResearchResponse with status
    func stopResearch(sessionId: String) async throws -> StopResearchResponse {
        return try await request(
            endpoint: "/api/research/\(sessionId)/stop",
            method: "POST",
            timeout: defaultTimeout
        )
    }

    /// Get the final report for a completed research session
    /// - Parameter sessionId: The session ID
    /// - Returns: ResearchReportResponse with final_report object
    func getResearchReport(sessionId: String) async throws -> ResearchReportResponse {
        return try await request(
            endpoint: "/api/research/\(sessionId)/report",
            method: "GET",
            timeout: defaultTimeout
        )
    }

    /// Export research data in specified format
    /// - Parameters:
    ///   - sessionId: The session ID
    ///   - format: Export format (e.g., "pdf", "docx", "json")
    ///   - options: Additional export options
    /// - Returns: Binary data of the exported file
    func exportResearch(
        sessionId: String,
        format: String,
        options: [String: Any] = [:]
    ) async throws -> Data {
        let requestBody = ExportRequest(
            sessionId: sessionId,
            format: format,
            options: options.mapValues { AnyCodable($0) }
        )
        let encoder = JSONEncoder()
        let bodyData = try encoder.encode(requestBody)

        return try await requestData(
            endpoint: "/api/export",
            method: "POST",
            body: bodyData,
            timeout: researchOperationTimeout
        )
    }

    /// Get available export formats
    /// - Returns: ExportFormatsResponse with list of supported formats
    func getExportFormats() async throws -> ExportFormatsResponse {
        return try await request(
            endpoint: "/api/export/formats",
            method: "GET",
            timeout: defaultTimeout
        )
    }

    /// Check API health status
    /// - Returns: HealthResponse with status
    func checkHealth() async throws -> HealthResponse {
        return try await request(
            endpoint: "/api/health",
            method: "GET",
            timeout: 10.0
        )
    }
}
