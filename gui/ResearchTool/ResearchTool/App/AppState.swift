import Foundation
import SwiftUI

/// Shared application state across views
@MainActor
class AppState: ObservableObject {

    // MARK: - Singleton

    static let shared = AppState()

    // MARK: - Published Properties

    /// Current connection status to backend
    @Published var isBackendConnected: Bool = false

    /// Current privacy mode setting
    @Published var currentPrivacyMode: PrivacyMode = .cloudAllowed

    /// Active research session ID if any
    @Published var activeResearchSessionId: String?

    /// Global error message
    @Published var globalError: String?

    /// Application version
    let appVersion: String = "1.0.0"

    /// Backend URL
    let backendURL: String = "ws://localhost:8002/ws/chat"

    // MARK: - User Preferences

    /// Remember last used privacy mode
    @AppStorage("lastPrivacyMode") var lastPrivacyModeRaw: String = PrivacyMode.cloudAllowed.rawValue

    /// Show advanced settings
    @AppStorage("showAdvancedSettings") var showAdvancedSettings: Bool = false

    /// Auto-connect on launch
    @AppStorage("autoConnect") var autoConnect: Bool = true

    // MARK: - Computed Properties

    var lastPrivacyMode: PrivacyMode {
        get {
            PrivacyMode(rawValue: lastPrivacyModeRaw) ?? .cloudAllowed
        }
        set {
            lastPrivacyModeRaw = newValue.rawValue
        }
    }

    // MARK: - Initialization

    private init() {
        // Restore last privacy mode
        currentPrivacyMode = lastPrivacyMode
    }

    // MARK: - Public Methods

    /// Update connection status
    func setConnected(_ connected: Bool) {
        isBackendConnected = connected
        if connected {
            globalError = nil
        }
    }

    /// Set global error
    func setError(_ error: String?) {
        globalError = error
    }

    /// Update privacy mode and persist
    func setPrivacyMode(_ mode: PrivacyMode) {
        currentPrivacyMode = mode
        lastPrivacyMode = mode
    }

    /// Start a new research session
    func startResearchSession(id: String) {
        activeResearchSessionId = id
    }

    /// End the current research session
    func endResearchSession() {
        activeResearchSessionId = nil
    }

    /// Check if a research session is active
    var isResearchActive: Bool {
        activeResearchSessionId != nil
    }
}
