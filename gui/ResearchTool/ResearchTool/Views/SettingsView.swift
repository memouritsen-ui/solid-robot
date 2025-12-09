import SwiftUI

/// Application settings view
struct SettingsView: View {
    @ObservedObject var appState = AppState.shared
    @State private var showingResetAlert = false

    var body: some View {
        Form {
            // Privacy Section
            Section("Privacy") {
                Picker("Default Privacy Mode", selection: $appState.currentPrivacyMode) {
                    ForEach(PrivacyMode.allCases, id: \.self) { mode in
                        HStack {
                            Image(systemName: mode.icon)
                            Text(mode.displayName)
                        }
                        .tag(mode)
                    }
                }
                .pickerStyle(.menu)
                .onChange(of: appState.currentPrivacyMode) { _, newValue in
                    appState.setPrivacyMode(newValue)
                }

                Text(privacyModeDescription)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            // Connection Section
            Section("Connection") {
                LabeledContent("Backend URL") {
                    Text(appState.backendURL)
                        .foregroundColor(.secondary)
                        .textSelection(.enabled)
                }

                Toggle("Auto-connect on launch", isOn: $appState.autoConnect)

                LabeledContent("Status") {
                    HStack {
                        Circle()
                            .fill(appState.isBackendConnected ? Color.green : Color.red)
                            .frame(width: 8, height: 8)
                        Text(appState.isBackendConnected ? "Connected" : "Disconnected")
                    }
                }
            }

            // Advanced Section
            Section("Advanced") {
                Toggle("Show advanced settings", isOn: $appState.showAdvancedSettings)

                if appState.showAdvancedSettings {
                    LabeledContent("App Version") {
                        Text(appState.appVersion)
                            .foregroundColor(.secondary)
                    }

                    Button("Reset All Settings", role: .destructive) {
                        showingResetAlert = true
                    }
                }
            }

            // About Section
            Section("About") {
                LabeledContent("Research Tool") {
                    Text("v\(appState.appVersion)")
                        .foregroundColor(.secondary)
                }

                Link("Documentation",
                     destination: URL(string: "https://github.com/memouritsen-ui/solid-robot")!)

                Link("Report Issue",
                     destination: URL(string: "https://github.com/memouritsen-ui/solid-robot/issues")!)
            }
        }
        .formStyle(.grouped)
        .navigationTitle("Settings")
        .alert("Reset Settings", isPresented: $showingResetAlert) {
            Button("Cancel", role: .cancel) {}
            Button("Reset", role: .destructive) {
                resetSettings()
            }
        } message: {
            Text("This will reset all settings to their default values.")
        }
    }

    private var privacyModeDescription: String {
        switch appState.currentPrivacyMode {
        case .localOnly:
            return "All processing stays on your device. Uses local Ollama models only."
        case .cloudAllowed:
            return "May use cloud AI for complex queries. Sensitive data detection enabled."
        }
    }

    private func resetSettings() {
        appState.setPrivacyMode(.cloudAllowed)
        appState.autoConnect = true
        appState.showAdvancedSettings = false
    }
}

// MARK: - PrivacyMode Extension

extension PrivacyMode: CaseIterable {
    public static var allCases: [PrivacyMode] {
        [.localOnly, .cloudAllowed]
    }

    var displayName: String {
        switch self {
        case .localOnly:
            return "Local Only"
        case .cloudAllowed:
            return "Cloud Allowed"
        }
    }

    var icon: String {
        switch self {
        case .localOnly:
            return "lock.shield"
        case .cloudAllowed:
            return "cloud"
        }
    }
}
