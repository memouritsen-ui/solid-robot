import SwiftUI

/// Main navigation view with sidebar and content
struct MainView: View {
    @StateObject private var appState = AppState.shared
    @State private var selectedTab: NavigationTab = .chat

    enum NavigationTab: String, CaseIterable {
        case chat = "Chat"
        case research = "Research"
        case settings = "Settings"

        var icon: String {
            switch self {
            case .chat: return "bubble.left.and.bubble.right"
            case .research: return "magnifyingglass"
            case .settings: return "gear"
            }
        }
    }

    var body: some View {
        NavigationSplitView {
            // Sidebar
            List(NavigationTab.allCases, id: \.self, selection: $selectedTab) { tab in
                Label(tab.rawValue, systemImage: tab.icon)
                    .tag(tab)
            }
            .navigationSplitViewColumnWidth(min: 180, ideal: 200)
            .listStyle(.sidebar)
        } detail: {
            // Content
            switch selectedTab {
            case .chat:
                ChatView()
            case .research:
                ResearchPlaceholderView()
            case .settings:
                SettingsView()
            }
        }
        .navigationSplitViewStyle(.balanced)
        .toolbar {
            ToolbarItem(placement: .automatic) {
                ConnectionStatusView()
            }
        }
    }
}

/// Connection status indicator for toolbar
struct ConnectionStatusView: View {
    @ObservedObject var appState = AppState.shared

    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(appState.isBackendConnected ? Color.green : Color.red)
                .frame(width: 8, height: 8)
            Text(appState.isBackendConnected ? "Connected" : "Offline")
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }
}

/// Placeholder for research view (to be implemented in Phase 4+)
struct ResearchPlaceholderView: View {
    @ObservedObject var appState = AppState.shared
    @State private var showingExportSheet: Bool = false

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "magnifyingglass.circle")
                .font(.system(size: 64))
                .foregroundColor(.secondary)

            Text("Research Mode")
                .font(.title)

            Text("Coming soon - Deep research with source analysis")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)

            // Export button (enabled when research session exists)
            if let sessionId = appState.activeResearchSessionId {
                Divider()
                    .padding(.vertical)

                Button(action: { showingExportSheet = true }) {
                    Label("Export Results", systemImage: "square.and.arrow.up")
                }
                .buttonStyle(.borderedProminent)
                .sheet(isPresented: $showingExportSheet) {
                    ExportView(sessionId: sessionId)
                }
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.windowBackgroundColor))
        .navigationTitle("Research")
        .toolbar {
            ToolbarItem(placement: .automatic) {
                if appState.activeResearchSessionId != nil {
                    Button(action: { showingExportSheet = true }) {
                        Image(systemName: "square.and.arrow.up")
                    }
                    .help("Export research results")
                }
            }
        }
    }
}
