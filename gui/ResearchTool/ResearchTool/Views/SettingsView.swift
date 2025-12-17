import SwiftUI

/// Application settings view with API key management
struct SettingsView: View {
    @ObservedObject var appState = AppState.shared
    @StateObject private var apiKeyManager = APIKeyManager()
    @State private var showingResetAlert = false
    @State private var showingDeleteKeysAlert = false

    var body: some View {
        Form {
            // API Keys Section
            Section("API Keys") {
                ForEach(KeychainService.APIKeyType.allCases, id: \.self) { keyType in
                    APIKeyRow(
                        keyType: keyType,
                        value: apiKeyManager.binding(for: keyType),
                        isConfigured: apiKeyManager.isConfigured(keyType),
                        onSave: { apiKeyManager.save(keyType) },
                        onTest: { await apiKeyManager.testKey(keyType) },
                        testStatus: apiKeyManager.testStatus[keyType] ?? .untested
                    )
                }

                HStack {
                    Button {
                        Task {
                            await apiKeyManager.saveAllAndRestart()
                        }
                    } label: {
                        if apiKeyManager.isRestartingBackend {
                            HStack {
                                ProgressView()
                                    .controlSize(.small)
                                Text("Restarting...")
                            }
                        } else {
                            Text("Save All Keys")
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(apiKeyManager.isRestartingBackend)

                    Button("Delete All Keys", role: .destructive) {
                        showingDeleteKeysAlert = true
                    }
                    .buttonStyle(.bordered)
                    .disabled(apiKeyManager.isRestartingBackend)
                }
                .padding(.top, 8)

                if !apiKeyManager.restartMessage.isEmpty {
                    Text(apiKeyManager.restartMessage)
                        .font(.caption)
                        .foregroundColor(.green)
                        .padding(.top, 4)
                }

                Text("Keys are stored securely in macOS Keychain. After saving, backend restarts to apply them.")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

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

                Button("Refresh Connection") {
                    Task {
                        await apiKeyManager.refreshBackendHealth()
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

                    LabeledContent("Ollama Status") {
                        HStack {
                            Circle()
                                .fill(apiKeyManager.ollamaHealthy ? Color.green : Color.orange)
                                .frame(width: 8, height: 8)
                            Text(apiKeyManager.ollamaHealthy ? "Healthy" : "Unknown")
                        }
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
        .onAppear {
            apiKeyManager.loadAllKeys()
            Task {
                await apiKeyManager.refreshBackendHealth()
            }
        }
        .alert("Reset Settings", isPresented: $showingResetAlert) {
            Button("Cancel", role: .cancel) {}
            Button("Reset", role: .destructive) {
                resetSettings()
            }
        } message: {
            Text("This will reset all settings to their default values.")
        }
        .alert("Delete All API Keys", isPresented: $showingDeleteKeysAlert) {
            Button("Cancel", role: .cancel) {}
            Button("Delete", role: .destructive) {
                apiKeyManager.deleteAllKeys()
            }
        } message: {
            Text("This will permanently delete all stored API keys from Keychain.")
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

// MARK: - API Key Row

struct APIKeyRow: View {
    let keyType: KeychainService.APIKeyType
    @Binding var value: String
    let isConfigured: Bool
    let onSave: () -> Void
    let onTest: () async -> Void
    let testStatus: APIKeyManager.TestStatus

    @State private var isEditing = false
    @State private var isTesting = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: keyType.icon)
                    .foregroundColor(statusColor)
                    .frame(width: 20)

                Text(keyType.displayName)
                    .font(.headline)

                Spacer()

                statusBadge
            }

            HStack {
                if isEditing {
                    SecureField(keyType.placeholder, text: $value)
                        .textFieldStyle(.roundedBorder)
                        .frame(maxWidth: .infinity)

                    Button("Save") {
                        onSave()
                        isEditing = false
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.small)

                    Button("Cancel") {
                        isEditing = false
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                } else {
                    Text(isConfigured ? "••••••••••••" : "Not configured")
                        .foregroundColor(isConfigured ? .primary : .secondary)
                        .frame(maxWidth: .infinity, alignment: .leading)

                    Button(isConfigured ? "Edit" : "Add") {
                        isEditing = true
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)

                    if isConfigured {
                        Button {
                            isTesting = true
                            Task {
                                await onTest()
                                isTesting = false
                            }
                        } label: {
                            if isTesting {
                                ProgressView()
                                    .controlSize(.small)
                            } else {
                                Text("Test")
                            }
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                        .disabled(isTesting)
                    }
                }
            }
        }
        .padding(.vertical, 4)
    }

    private var statusColor: Color {
        switch testStatus {
        case .untested:
            return isConfigured ? .blue : .gray
        case .valid:
            return .green
        case .invalid:
            return .red
        case .testing:
            return .orange
        }
    }

    @ViewBuilder
    private var statusBadge: some View {
        switch testStatus {
        case .untested:
            if isConfigured {
                Text("Saved")
                    .font(.caption)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.blue.opacity(0.2))
                    .foregroundColor(.blue)
                    .cornerRadius(4)
            }
        case .valid:
            Text("Valid")
                .font(.caption)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(Color.green.opacity(0.2))
                .foregroundColor(.green)
                .cornerRadius(4)
        case .invalid:
            Text("Invalid")
                .font(.caption)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(Color.red.opacity(0.2))
                .foregroundColor(.red)
                .cornerRadius(4)
        case .testing:
            Text("Testing...")
                .font(.caption)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(Color.orange.opacity(0.2))
                .foregroundColor(.orange)
                .cornerRadius(4)
        }
    }
}

// MARK: - API Key Manager

@MainActor
class APIKeyManager: ObservableObject {

    enum TestStatus {
        case untested
        case testing
        case valid
        case invalid
    }

    @Published var keys: [KeychainService.APIKeyType: String] = [:]
    @Published var testStatus: [KeychainService.APIKeyType: TestStatus] = [:]
    @Published var ollamaHealthy: Bool = false
    @Published var isRestartingBackend: Bool = false
    @Published var restartMessage: String = ""

    private let keychain = KeychainService.shared
    private let backendLauncher = BackendLauncher.shared

    init() {
        loadAllKeys()
    }

    func binding(for type: KeychainService.APIKeyType) -> Binding<String> {
        Binding(
            get: { self.keys[type] ?? "" },
            set: { self.keys[type] = $0 }
        )
    }

    func isConfigured(_ type: KeychainService.APIKeyType) -> Bool {
        keychain.hasKey(for: type)
    }

    func loadAllKeys() {
        for type in KeychainService.APIKeyType.allCases {
            if let key = keychain.getKey(for: type) {
                keys[type] = key
            }
        }
    }

    func save(_ type: KeychainService.APIKeyType) {
        if let key = keys[type], !key.isEmpty {
            keychain.saveKey(key, for: type)
            testStatus[type] = .untested
        }
    }

    func saveAll() {
        for type in KeychainService.APIKeyType.allCases {
            if let key = keys[type], !key.isEmpty {
                keychain.saveKey(key, for: type)
            }
        }
    }

    /// Save all keys and restart backend to apply them
    func saveAllAndRestart() async {
        saveAll()
        restartMessage = "Restarting backend to apply new API keys..."
        isRestartingBackend = true

        await backendLauncher.restartBackend()

        isRestartingBackend = false
        restartMessage = "Backend restarted with new API keys"

        // Clear message after 3 seconds
        try? await Task.sleep(nanoseconds: 3_000_000_000)
        restartMessage = ""
    }

    func deleteAllKeys() {
        keychain.deleteAllKeys()
        keys.removeAll()
        testStatus.removeAll()
    }

    func testKey(_ type: KeychainService.APIKeyType) async {
        testStatus[type] = .testing

        do {
            let health = try await APIClient.shared.checkDetailedHealth()

            // Check specific provider status based on components
            if let components = health.components {
                switch type {
                case .anthropic:
                    if let anthropic = components["anthropic"] {
                        testStatus[type] = anthropic.status == "healthy" ? .valid : .invalid
                    } else {
                        testStatus[type] = .invalid
                    }
                case .tavily:
                    if let searchProviders = components["search_providers"],
                       searchProviders.status == "healthy" {
                        // Tavily is typically part of search_providers
                        testStatus[type] = .valid
                    } else {
                        testStatus[type] = .invalid
                    }
                case .brave, .exa:
                    // Similar check for other providers
                    if let searchProviders = components["search_providers"],
                       searchProviders.status == "healthy" {
                        testStatus[type] = .valid
                    } else {
                        testStatus[type] = .invalid
                    }
                }
            } else {
                testStatus[type] = .invalid
            }
        } catch {
            print("[APIKeyManager] Test key failed: \(error.localizedDescription)")
            testStatus[type] = .invalid
        }
    }

    func refreshBackendHealth() async {
        do {
            let health = try await APIClient.shared.checkDetailedHealth()

            // Update connection status
            AppState.shared.setConnected(health.status == "healthy" || health.status == "degraded")

            // Check Ollama status
            if let components = health.components,
               let ollama = components["ollama"] {
                ollamaHealthy = ollama.status == "healthy"
            } else {
                ollamaHealthy = false
            }
        } catch {
            AppState.shared.setConnected(false)
            ollamaHealthy = false
        }
    }
}
