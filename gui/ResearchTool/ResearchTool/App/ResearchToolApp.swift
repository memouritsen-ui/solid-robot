import SwiftUI

@main
struct ResearchToolApp: App {
    @StateObject private var backendLauncher = BackendLauncher.shared
    @StateObject private var appState = AppState.shared

    var body: some Scene {
        WindowGroup {
            MainContentView()
                .environmentObject(backendLauncher)
                .environmentObject(appState)
                .task {
                    // Auto-start backend when app launches
                    await backendLauncher.startBackendIfNeeded()
                }
        }
        .windowStyle(.automatic)
        .defaultSize(width: 900, height: 700)
        .commands {
            CommandGroup(replacing: .appInfo) {
                Button("Om Research Tool") {
                    NSApplication.shared.orderFrontStandardAboutPanel(
                        options: [
                            .applicationName: "Research Tool",
                            .applicationVersion: appState.appVersion,
                            .credits: NSAttributedString(string: "Professional research assistant med privacy-first design.")
                        ]
                    )
                }
            }
        }
    }
}

/// Main content view with backend status
struct MainContentView: View {
    @EnvironmentObject var backendLauncher: BackendLauncher
    @EnvironmentObject var appState: AppState

    var body: some View {
        ZStack {
            if backendLauncher.isRunning {
                NavigationStack {
                    MainView()
                }
            } else {
                // Show loading screen while backend starts
                VStack(spacing: 20) {
                    ProgressView()
                        .scaleEffect(1.5)

                    Text(backendLauncher.statusMessage)
                        .font(.headline)

                    Text("Research Tool starter op...")
                        .font(.subheadline)
                        .foregroundColor(.secondary)

                    if backendLauncher.statusMessage.contains("kunne ikke") {
                        Button("Prøv igen") {
                            Task {
                                await backendLauncher.startBackendIfNeeded()
                            }
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }
}
