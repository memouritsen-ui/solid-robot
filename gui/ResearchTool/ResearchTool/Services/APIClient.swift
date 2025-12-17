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
    let currentPhase: String
    let entitiesFound: [EntityItem]
    let factsExtracted: [FactItem]
    let sourcesQueried: [String]
    let saturationMetrics: SaturationMetrics?
    let shouldStop: Bool

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case currentPhase = "current_phase"
        case entitiesFound = "entities_found"
        case factsExtracted = "facts_extracted"
        case sourcesQueried = "sources_queried"
        case saturationMetrics = "saturation_metrics"
        case shouldStop = "should_stop"
    }
}

struct EntityItem: Codable {
    let name: String?
    let type: String?
}

struct FactItem: Codable {
    let statement: String?
    let confidence: Double?
    let sources: [String]?
}

struct SaturationMetrics: Codable {
    let entityGrowth: Double?
    let factGrowth: Double?
    let sourceExhaustion: Double?
    let overallSaturation: Double?

    enum CodingKeys: String, CodingKey {
        case entityGrowth = "entity_growth"
        case factGrowth = "fact_growth"
        case sourceExhaustion = "source_exhaustion"
        case overallSaturation = "overall_saturation"
    }
}

struct StopResearchResponse: Codable {
    let status: String
}

struct ResearchReportResponse: Codable {
    let sessionId: String
    let finalReport: FinalReport?

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case finalReport = "final_report"
    }
}

struct FinalReport: Codable {
    let summary: String?
    let sections: [[String: String]]?
    let sources: [String]?
}

struct ExportFormatsResponse: Codable {
    let formats: [String]
}

struct HealthResponse: Codable {
    let status: String
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

    private init(baseURL: String = "http://localhost:8002") {
        self.baseURL = baseURL
    }

    // MARK: - Research Endpoints

    /// Start a new research session
    func startResearch(query: String, privacyMode: String) async throws -> StartResearchResponse {
        let body: [String: Any] = [
            "query": query,
            "privacy_mode": privacyMode
        ]
        return try await post(
            path: "/api/research/start",
            body: body,
            timeout: researchTimeout
        )
    }

    /// Get status of a research session
    func getResearchStatus(sessionId: String) async throws -> ResearchStatusResponse {
        return try await get(
            path: "/api/research/\(sessionId)/status",
            timeout: defaultTimeout
        )
    }

    /// Stop a research session
    func stopResearch(sessionId: String) async throws -> StopResearchResponse {
        return try await post(
            path: "/api/research/\(sessionId)/stop",
            body: [:],
            timeout: defaultTimeout
        )
    }

    /// Get final research report
    func getResearchReport(sessionId: String) async throws -> ResearchReportResponse {
        return try await get(
            path: "/api/research/\(sessionId)/report",
            timeout: researchTimeout
        )
    }

    // MARK: - Export Endpoints

    /// Export research results as binary data
    func exportResearch(
        sessionId: String,
        format: String,
        includeMetadata: Bool = true,
        includeSources: Bool = true
    ) async throws -> Data {
        let body: [String: Any] = [
            "session_id": sessionId,
            "format": format,
            "options": [
                "include_metadata": includeMetadata,
                "include_sources": includeSources
            ]
        ]
        return try await postRaw(path: "/api/export", body: body)
    }

    /// Get available export formats
    func getExportFormats() async throws -> ExportFormatsResponse {
        return try await get(path: "/api/export/formats", timeout: defaultTimeout)
    }

    // MARK: - Health Endpoint

    /// Check backend health
    func checkHealth() async throws -> HealthResponse {
        return try await get(path: "/api/health", timeout: 5)
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
            throw APIError.decodingError(error)
        } catch {
            throw APIError.networkError(error)
        }
    }
}
