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
                ResearchView()
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

// ResearchPlaceholderView removed - now using ResearchView
