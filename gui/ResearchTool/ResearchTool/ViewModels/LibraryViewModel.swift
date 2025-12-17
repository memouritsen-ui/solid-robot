import Foundation
import SwiftUI

/// ViewModel managing the research library - stored sessions with search
@MainActor
class LibraryViewModel: ObservableObject {

    // MARK: - Published Properties

    /// All sessions in the library (paginated)
    @Published var sessions: [LibrarySessionSummary] = []

    /// Search results when searching
    @Published var searchResults: [LibrarySearchResult] = []

    /// Currently selected session for detail view
    @Published var selectedSession: LibrarySessionDetail?

    /// Library statistics
    @Published var stats: LibraryStatsResponse?

    /// Current search query
    @Published var searchQuery: String = ""

    /// Whether we're currently loading
    @Published var isLoading: Bool = false

    /// Whether we're searching (vs browsing)
    @Published var isSearching: Bool = false

    /// Error message to display
    @Published var errorMessage: String?

    /// Whether to show delete confirmation
    @Published var showingDeleteConfirmation: Bool = false

    /// Session pending deletion
    @Published var sessionToDelete: String?

    // MARK: - Pagination

    @Published var currentPage: Int = 0
    @Published var totalSessions: Int = 0
    @Published var hasMorePages: Bool = false

    private let pageSize = 20

    // MARK: - Computed Properties

    /// Whether the library is empty
    var isEmpty: Bool {
        sessions.isEmpty && searchResults.isEmpty && !isLoading
    }

    /// Items to display (search results or all sessions)
    var displayItems: [LibrarySessionSummary] {
        if isSearching && !searchQuery.isEmpty {
            // Convert search results to summaries for display
            return searchResults.map { result in
                LibrarySessionSummary(
                    sessionId: result.sessionId,
                    query: result.query,
                    domain: "general",
                    status: "completed",
                    factsCount: 0,
                    sourcesCount: 0,
                    confidenceScore: nil,
                    startedAt: result.startedAt,
                    completedAt: nil
                )
            }
        }
        return sessions
    }

    // MARK: - Public Methods

    /// Load initial library data
    func loadLibrary() async {
        isLoading = true
        errorMessage = nil

        do {
            async let sessionsTask = APIClient.shared.listLibrarySessions(
                offset: 0,
                limit: pageSize
            )
            async let statsTask = APIClient.shared.getLibraryStats()

            let (sessionsResponse, statsResponse) = try await (sessionsTask, statsTask)

            sessions = sessionsResponse.sessions
            totalSessions = sessionsResponse.total
            hasMorePages = sessionsResponse.sessions.count == pageSize
            currentPage = 0
            stats = statsResponse

            print("[LibraryViewModel] Loaded \(sessions.count) sessions, total: \(totalSessions)")

        } catch {
            handleError(error)
        }

        isLoading = false
    }

    /// Load more sessions (pagination)
    func loadMoreIfNeeded(currentItem: LibrarySessionSummary?) async {
        guard let item = currentItem else { return }
        guard !isLoading && hasMorePages else { return }

        // Check if we're near the end of the list
        let thresholdIndex = sessions.index(sessions.endIndex, offsetBy: -5)
        guard sessions.firstIndex(where: { $0.id == item.id }) ?? 0 >= thresholdIndex else {
            return
        }

        await loadNextPage()
    }

    /// Load next page of sessions
    func loadNextPage() async {
        guard !isLoading && hasMorePages else { return }

        isLoading = true
        let nextPage = currentPage + 1
        let offset = nextPage * pageSize

        do {
            let response = try await APIClient.shared.listLibrarySessions(
                offset: offset,
                limit: pageSize
            )

            sessions.append(contentsOf: response.sessions)
            currentPage = nextPage
            hasMorePages = response.sessions.count == pageSize

            print("[LibraryViewModel] Loaded page \(nextPage), now have \(sessions.count) sessions")

        } catch {
            handleError(error)
        }

        isLoading = false
    }

    /// Search the library
    func search() async {
        let query = searchQuery.trimmingCharacters(in: .whitespacesAndNewlines)

        if query.isEmpty {
            isSearching = false
            searchResults = []
            return
        }

        isSearching = true
        isLoading = true
        errorMessage = nil

        do {
            let response = try await APIClient.shared.searchLibrary(
                query: query,
                limit: 50
            )
            searchResults = response.results

            print("[LibraryViewModel] Search '\(query)' returned \(searchResults.count) results")

        } catch {
            handleError(error)
        }

        isLoading = false
    }

    /// Clear search and return to browse mode
    func clearSearch() {
        searchQuery = ""
        searchResults = []
        isSearching = false
    }

    /// Load full details for a session
    func loadSessionDetail(sessionId: String) async {
        isLoading = true
        errorMessage = nil

        do {
            selectedSession = try await APIClient.shared.getLibrarySession(sessionId: sessionId)
            print("[LibraryViewModel] Loaded session detail: \(sessionId)")

        } catch {
            handleError(error)
        }

        isLoading = false
    }

    /// Request deletion of a session (shows confirmation)
    func requestDelete(sessionId: String) {
        sessionToDelete = sessionId
        showingDeleteConfirmation = true
    }

    /// Confirm and execute deletion
    func confirmDelete() async {
        guard let sessionId = sessionToDelete else { return }

        isLoading = true
        errorMessage = nil

        do {
            _ = try await APIClient.shared.deleteLibrarySession(sessionId: sessionId)

            // Remove from local list
            sessions.removeAll { $0.sessionId == sessionId }
            searchResults.removeAll { $0.sessionId == sessionId }
            totalSessions -= 1

            // Clear selection if deleted session was selected
            if selectedSession?.sessionId == sessionId {
                selectedSession = nil
            }

            // Reload stats
            stats = try await APIClient.shared.getLibraryStats()

            print("[LibraryViewModel] Deleted session: \(sessionId)")

        } catch {
            handleError(error)
        }

        sessionToDelete = nil
        showingDeleteConfirmation = false
        isLoading = false
    }

    /// Cancel deletion
    func cancelDelete() {
        sessionToDelete = nil
        showingDeleteConfirmation = false
    }

    /// Refresh the library
    func refresh() async {
        if isSearching && !searchQuery.isEmpty {
            await search()
        } else {
            await loadLibrary()
        }
    }

    // MARK: - Private Methods

    private func handleError(_ error: Error) {
        if let apiError = error as? APIError {
            errorMessage = apiError.localizedDescription
        } else {
            errorMessage = error.localizedDescription
        }
        print("[LibraryViewModel] Error: \(errorMessage ?? "unknown")")
    }
}
