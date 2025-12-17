import Foundation

/// Protocol for receiving WebSocket events
@MainActor
protocol WebSocketClientDelegate: AnyObject {
    func webSocketDidConnect()
    func webSocketDidDisconnect()
    func webSocketDidFail(error: Error)
    func webSocketDidReceiveModelInfo(model: String, complexity: String, privacyMode: String)
    func webSocketDidReceiveToken(_ token: String)
    func webSocketDidComplete(model: String, reasoning: String)
    func webSocketDidReceiveError(_ message: String)
}

/// WebSocket client for real-time chat communication with the backend.
/// Handles connection lifecycle, message sending, and streaming token reception.
/// Includes automatic reconnection and keepalive ping.
final class WebSocketClient: NSObject, @unchecked Sendable {

    // MARK: - Types

    /// Message types received from server
    private enum ServerMessageType: String {
        case modelInfo = "model_info"
        case token
        case done
        case error
    }

    /// Parsed server message
    private struct ServerMessage {
        let type: ServerMessageType
        let content: String?
        let model: String?
        let reasoning: String?
        let complexity: String?
        let privacyMode: String?
        let errorMessage: String?
    }

    // MARK: - Properties

    private var webSocket: URLSessionWebSocketTask?
    private var session: URLSession?
    private let baseURL: String

    weak var delegate: WebSocketClientDelegate?

    // Reconnection properties
    private var isIntentionalDisconnect = false
    private var reconnectAttempts = 0
    private let maxReconnectAttempts = 10
    private var reconnectTask: Task<Void, Never>?

    // Keepalive properties
    private var pingTask: Task<Void, Never>?
    private let pingInterval: TimeInterval = 30  // Send ping every 30 seconds

    // MARK: - Initialization

    init(baseURL: String = "ws://localhost:8000") {
        self.baseURL = baseURL
        super.init()
    }

    deinit {
        reconnectTask?.cancel()
        pingTask?.cancel()
    }

    // MARK: - Connection Management

    /// Connect to the WebSocket server
    func connect() {
        guard webSocket == nil else { return }

        isIntentionalDisconnect = false

        guard let url = URL(string: "\(baseURL)/ws/chat") else {
            Task { @MainActor in
                delegate?.webSocketDidFail(error: URLError(.badURL))
            }
            return
        }

        session = URLSession(configuration: .default, delegate: self, delegateQueue: nil)
        webSocket = session?.webSocketTask(with: url)
        webSocket?.resume()

        startReceiving()
        startPingTimer()
    }

    /// Disconnect from the WebSocket server
    func disconnect() {
        isIntentionalDisconnect = true
        reconnectTask?.cancel()
        reconnectTask = nil
        pingTask?.cancel()
        pingTask = nil

        webSocket?.cancel(with: .goingAway, reason: nil)
        webSocket = nil
        session = nil

        Task { @MainActor in
            delegate?.webSocketDidDisconnect()
        }
    }

    /// Check if currently connected
    var isConnected: Bool {
        webSocket != nil && webSocket?.state == .running
    }

    // MARK: - Reconnection

    private func scheduleReconnect() {
        guard !isIntentionalDisconnect else { return }
        guard reconnectAttempts < maxReconnectAttempts else {
            print("[WebSocket] Max reconnect attempts reached")
            return
        }

        reconnectAttempts += 1

        // Exponential backoff: 1s, 2s, 4s, 8s, 16s, max 30s
        let delay = min(pow(2.0, Double(reconnectAttempts - 1)), 30.0)
        print("[WebSocket] Scheduling reconnect attempt \(reconnectAttempts) in \(delay)s")

        reconnectTask = Task {
            try? await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))

            guard !Task.isCancelled && !isIntentionalDisconnect else { return }

            // Clear old connection
            webSocket = nil
            session = nil

            // Attempt reconnect
            connect()
        }
    }

    private func resetReconnectAttempts() {
        reconnectAttempts = 0
        reconnectTask?.cancel()
        reconnectTask = nil
    }

    // MARK: - Keepalive Ping

    private func startPingTimer() {
        pingTask?.cancel()

        pingTask = Task {
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: UInt64(pingInterval * 1_000_000_000))

                guard !Task.isCancelled, let ws = webSocket else { break }

                ws.sendPing { [weak self] error in
                    if let error = error {
                        print("[WebSocket] Ping failed: \(error.localizedDescription)")
                        // Connection likely dead, trigger reconnect
                        self?.handleConnectionLost()
                    }
                }
            }
        }
    }

    private func handleConnectionLost() {
        guard !isIntentionalDisconnect else { return }

        pingTask?.cancel()
        webSocket?.cancel(with: .abnormalClosure, reason: nil)
        webSocket = nil
        session = nil

        Task { @MainActor in
            delegate?.webSocketDidDisconnect()
        }

        scheduleReconnect()
    }

    // MARK: - Message Sending

    /// Send a chat message to the server
    /// - Parameters:
    ///   - message: The user's message text
    ///   - privacyMode: Privacy mode setting ("local_only" or "cloud_allowed")
    func send(message: String, privacyMode: String = "cloud_allowed") {
        guard let webSocket = webSocket else { return }

        let payload: [String: Any] = [
            "message": message,
            "privacy_mode": privacyMode
        ]

        guard let data = try? JSONSerialization.data(withJSONObject: payload),
              let jsonString = String(data: data, encoding: .utf8) else {
            return
        }

        webSocket.send(.string(jsonString)) { [weak self] error in
            if let error = error {
                Task { @MainActor in
                    self?.delegate?.webSocketDidReceiveError("Failed to send: \(error.localizedDescription)")
                }
                // Connection might be broken
                self?.handleConnectionLost()
            }
        }
    }

    // MARK: - Message Receiving

    private func startReceiving() {
        webSocket?.receive { [weak self] result in
            switch result {
            case .success(let message):
                self?.handleMessage(message)
                self?.startReceiving()  // Continue receiving
            case .failure(let error):
                print("[WebSocket] Receive error: \(error.localizedDescription)")
                Task { @MainActor in
                    self?.delegate?.webSocketDidFail(error: error)
                }
                self?.handleConnectionLost()
            }
        }
    }

    private func handleMessage(_ message: URLSessionWebSocketTask.Message) {
        switch message {
        case .string(let text):
            if let parsed = parseServerMessage(text) {
                dispatchMessage(parsed)
            }
        case .data(let data):
            if let text = String(data: data, encoding: .utf8),
               let parsed = parseServerMessage(text) {
                dispatchMessage(parsed)
            }
        @unknown default:
            break
        }
    }

    private func parseServerMessage(_ text: String) -> ServerMessage? {
        guard let data = text.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let typeString = json["type"] as? String,
              let type = ServerMessageType(rawValue: typeString) else {
            return nil
        }

        return ServerMessage(
            type: type,
            content: json["content"] as? String,
            model: json["model"] as? String,
            reasoning: json["reasoning"] as? String,
            complexity: json["complexity"] as? String,
            privacyMode: json["privacy_mode"] as? String,
            errorMessage: json["message"] as? String
        )
    }

    private func dispatchMessage(_ message: ServerMessage) {
        Task { @MainActor in
            switch message.type {
            case .modelInfo:
                if let model = message.model,
                   let complexity = message.complexity,
                   let privacyMode = message.privacyMode {
                    delegate?.webSocketDidReceiveModelInfo(
                        model: model,
                        complexity: complexity,
                        privacyMode: privacyMode
                    )
                }

            case .token:
                if let content = message.content {
                    delegate?.webSocketDidReceiveToken(content)
                }

            case .done:
                let model = message.model ?? "unknown"
                let reasoning = message.reasoning ?? ""
                delegate?.webSocketDidComplete(model: model, reasoning: reasoning)

            case .error:
                let errorMsg = message.errorMessage ?? "Unknown error"
                delegate?.webSocketDidReceiveError(errorMsg)
            }
        }
    }
}

// MARK: - URLSessionWebSocketDelegate

extension WebSocketClient: URLSessionWebSocketDelegate {
    func urlSession(
        _ session: URLSession,
        webSocketTask: URLSessionWebSocketTask,
        didOpenWithProtocol protocol: String?
    ) {
        print("[WebSocket] Connected successfully")
        resetReconnectAttempts()

        Task { @MainActor in
            delegate?.webSocketDidConnect()
        }
    }

    func urlSession(
        _ session: URLSession,
        webSocketTask: URLSessionWebSocketTask,
        didCloseWith closeCode: URLSessionWebSocketTask.CloseCode,
        reason: Data?
    ) {
        print("[WebSocket] Closed with code: \(closeCode.rawValue)")
        webSocket = nil
        pingTask?.cancel()

        Task { @MainActor in
            delegate?.webSocketDidDisconnect()
        }

        // Auto-reconnect if not intentional
        if !isIntentionalDisconnect {
            scheduleReconnect()
        }
    }

    func urlSession(
        _ session: URLSession,
        task: URLSessionTask,
        didCompleteWithError error: Error?
    ) {
        if let error = error {
            print("[WebSocket] Connection error: \(error.localizedDescription)")
            Task { @MainActor in
                delegate?.webSocketDidFail(error: error)
            }

            // Auto-reconnect on error
            if !isIntentionalDisconnect {
                scheduleReconnect()
            }
        }
    }
}
