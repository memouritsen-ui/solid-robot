import SwiftUI

/// Library view for browsing and searching past research sessions
struct LibraryView: View {
    @StateObject private var viewModel = LibraryViewModel()
    @State private var selectedSessionId: String?

    var body: some View {
        NavigationSplitView {
            // Sidebar: Session list
            sidebarContent
        } detail: {
            // Detail: Selected session
            detailContent
        }
        .navigationTitle("Research Library")
        .task {
            await viewModel.loadLibrary()
        }
        .refreshable {
            await viewModel.refresh()
        }
        .alert("Delete Session?", isPresented: $viewModel.showingDeleteConfirmation) {
            Button("Cancel", role: .cancel) {
                viewModel.cancelDelete()
            }
            Button("Delete", role: .destructive) {
                Task {
                    await viewModel.confirmDelete()
                }
            }
        } message: {
            Text("This will permanently delete this research session and all its data.")
        }
    }

    // MARK: - Sidebar Content

    private var sidebarContent: some View {
        VStack(spacing: 0) {
            // Search bar
            searchBar

            // Stats header
            if let stats = viewModel.stats {
                statsHeader(stats)
            }

            Divider()

            // Session list or empty state
            if viewModel.isEmpty {
                emptyState
            } else {
                sessionList
            }
        }
    }

    // MARK: - Search Bar

    private var searchBar: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.secondary)

            TextField("Search library...", text: $viewModel.searchQuery)
                .textFieldStyle(.plain)
                .onSubmit {
                    Task {
                        await viewModel.search()
                    }
                }

            if !viewModel.searchQuery.isEmpty {
                Button {
                    viewModel.clearSearch()
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(8)
        .background(Color(.textBackgroundColor))
        .cornerRadius(8)
        .padding()
    }

    // MARK: - Stats Header

    private func statsHeader(_ stats: LibraryStatsResponse) -> some View {
        HStack(spacing: 16) {
            statItem(value: "\(stats.totalSessions)", label: "Sessions")
            statItem(value: "\(stats.totalFacts)", label: "Facts")
            statItem(value: "\(stats.totalSources)", label: "Sources")
            if let confidence = stats.averageConfidence {
                statItem(value: String(format: "%.0f%%", confidence * 100), label: "Avg Conf")
            }
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .background(Color(.controlBackgroundColor))
    }

    private func statItem(value: String, label: String) -> some View {
        VStack(spacing: 2) {
            Text(value)
                .font(.headline)
            Text(label)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
    }

    // MARK: - Session List

    private var sessionList: some View {
        List(viewModel.displayItems, selection: $selectedSessionId) { session in
            sessionRow(session)
                .tag(session.sessionId)
                .contextMenu {
                    Button(role: .destructive) {
                        viewModel.requestDelete(sessionId: session.sessionId)
                    } label: {
                        Label("Delete", systemImage: "trash")
                    }
                }
                .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                    Button(role: .destructive) {
                        viewModel.requestDelete(sessionId: session.sessionId)
                    } label: {
                        Label("Delete", systemImage: "trash")
                    }
                }
                .task {
                    await viewModel.loadMoreIfNeeded(currentItem: session)
                }
        }
        .listStyle(.sidebar)
        .overlay {
            if viewModel.isLoading {
                ProgressView()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(Color.black.opacity(0.1))
            }
        }
        .onChange(of: selectedSessionId) { _, newValue in
            if let sessionId = newValue {
                Task {
                    await viewModel.loadSessionDetail(sessionId: sessionId)
                }
            }
        }
    }

    // MARK: - Session Row

    private func sessionRow(_ session: LibrarySessionSummary) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(session.query)
                .font(.headline)
                .lineLimit(2)

            HStack(spacing: 8) {
                // Domain badge
                Text(session.domain)
                    .font(.caption)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.blue.opacity(0.2))
                    .foregroundColor(.blue)
                    .cornerRadius(4)

                // Facts count
                Label("\(session.factsCount)", systemImage: "doc.text.fill")
                    .font(.caption)
                    .foregroundColor(.secondary)

                // Sources count
                Label("\(session.sourcesCount)", systemImage: "link")
                    .font(.caption)
                    .foregroundColor(.secondary)

                Spacer()

                // Confidence badge
                if let confidence = session.confidenceScore {
                    Text(String(format: "%.0f%%", confidence * 100))
                        .font(.caption)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(confidenceColor(confidence).opacity(0.2))
                        .foregroundColor(confidenceColor(confidence))
                        .cornerRadius(4)
                }
            }

            Text(session.formattedDate)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 4)
    }

    private func confidenceColor(_ confidence: Double) -> Color {
        if confidence >= 0.8 { return .green }
        if confidence >= 0.6 { return .orange }
        return .red
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "books.vertical")
                .font(.system(size: 48))
                .foregroundColor(.secondary)

            Text("No Research Sessions")
                .font(.headline)

            Text("Complete a research query to save it to your library.")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }

    // MARK: - Detail Content

    @ViewBuilder
    private var detailContent: some View {
        if let session = viewModel.selectedSession {
            SessionDetailView(session: session)
        } else {
            VStack(spacing: 16) {
                Image(systemName: "doc.text.magnifyingglass")
                    .font(.system(size: 48))
                    .foregroundColor(.secondary)

                Text("Select a Session")
                    .font(.headline)

                Text("Choose a research session from the list to view its details.")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }
}

// MARK: - Preview

#if DEBUG
struct LibraryView_Previews: PreviewProvider {
    static var previews: some View {
        LibraryView()
    }
}
#endif
