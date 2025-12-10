import Foundation

/// Manages the Python backend process lifecycle
@MainActor
class BackendLauncher: ObservableObject {

    static let shared = BackendLauncher()

    @Published var isRunning: Bool = false
    @Published var statusMessage: String = "Backend ikke startet"

    private var backendProcess: Process?
    private var outputPipe: Pipe?

    /// Path to the backend directory with robust resolution
    private var backendPath: String {
        // Priority 1: Environment variable
        if let envPath = ProcessInfo.processInfo.environment["RESEARCH_TOOL_BACKEND_PATH"] {
            if FileManager.default.fileExists(atPath: envPath) {
                print("[BackendLauncher] Using env path: \(envPath)")
                return envPath
            }
            print("[BackendLauncher] WARNING: Env path not found: \(envPath)")
        }

        // Priority 2: App bundle (for distributed app)
        if let bundlePath = Bundle.main.resourcePath {
            let bundleBackendPath = (bundlePath as NSString)
                .deletingLastPathComponent
                .appending("/backend")
            if FileManager.default.fileExists(atPath: bundleBackendPath) {
                print("[BackendLauncher] Using bundle path: \(bundleBackendPath)")
                return bundleBackendPath
            }
        }

        // Priority 3: UserDefaults custom path
        if let customPath = UserDefaults.standard.string(forKey: "backendPath") {
            if FileManager.default.fileExists(atPath: customPath) {
                print("[BackendLauncher] Using custom path: \(customPath)")
                return customPath
            }
            print("[BackendLauncher] WARNING: Custom path not found: \(customPath)")
        }

        // Priority 4: Known development paths (TRY BOTH CASINGS)
        let devPaths = [
            "/Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend",  // Uppercase (CORRECT)
            "/Users/madsbruusgaard-mouritsen/solid-robot/backend",  // Lowercase (fallback)
            NSHomeDirectory() + "/SOLID-ROBOT/backend",
            NSHomeDirectory() + "/solid-robot/backend"
        ]

        for path in devPaths {
            if FileManager.default.fileExists(atPath: path) {
                print("[BackendLauncher] Using dev path: \(path)")
                return path
            }
        }

        // Nothing found - return first dev path and let it fail with clear error
        let fallback = devPaths[0]
        print("[BackendLauncher] ERROR: No valid backend path found. Tried: \(devPaths)")
        return fallback
    }

    private init() {}

    /// Check if backend is already running by testing the health endpoint
    func checkBackendHealth() async -> Bool {
        guard let url = URL(string: "http://localhost:8000/api/health") else {
            return false
        }

        do {
            let (_, response) = try await URLSession.shared.data(from: url)
            if let httpResponse = response as? HTTPURLResponse {
                return httpResponse.statusCode == 200
            }
        } catch {
            // Backend not responding
        }
        return false
    }

    /// Start the backend if not already running
    func startBackendIfNeeded() async {
        // First check if backend is already running
        if await checkBackendHealth() {
            isRunning = true
            statusMessage = "Backend kører allerede"
            return
        }

        statusMessage = "Starter backend..."

        // Start the backend process
        await startBackendProcess()

        // Wait for backend to be ready (max 30 seconds)
        for _ in 0..<30 {
            try? await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
            if await checkBackendHealth() {
                isRunning = true
                statusMessage = "Backend kører"
                return
            }
        }

        statusMessage = "Backend kunne ikke startes. Tjek at backend findes i: \(backendPath)"
        print("[BackendLauncher] FATAL: Backend startup failed after 30s. Path: \(backendPath)")
    }

    /// Start the backend process
    private func startBackendProcess() async {
        let process = Process()

        // Use zsh to ensure PATH is set correctly
        process.executableURL = URL(fileURLWithPath: "/bin/zsh")
        process.arguments = ["-l", "-c", "cd \(backendPath) && uv run python -m uvicorn src.research_tool.main:app --host 127.0.0.1 --port 8000"]

        // Set up output pipe for logging
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        // Read output in background
        pipe.fileHandleForReading.readabilityHandler = { handle in
            let data = handle.availableData
            if let output = String(data: data, encoding: .utf8), !output.isEmpty {
                print("[Backend] \(output)")
            }
        }

        do {
            try process.run()
            self.backendProcess = process
            self.outputPipe = pipe
        } catch {
            print("Failed to start backend: \(error)")
            statusMessage = "Fejl: \(error.localizedDescription)"
        }
    }

    /// Stop the backend process
    func stopBackend() {
        if let process = backendProcess, process.isRunning {
            process.terminate()
            backendProcess = nil
        }
        outputPipe?.fileHandleForReading.readabilityHandler = nil
        outputPipe = nil
        isRunning = false
        statusMessage = "Backend stoppet"
    }

    deinit {
        // Clean up when app closes
        backendProcess?.terminate()
    }
}
