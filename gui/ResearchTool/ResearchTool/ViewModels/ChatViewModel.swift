import Foundation
import Combine

/// ViewModel managing chat state and WebSocket communication
@MainActor
class ChatViewModel: ObservableObject, WebSocketClientDelegate {

    // MARK: - Published Properties

    @Published var messages: [Message] = []
    @Published var currentStreamingContent: String = ""
    @Published var isLoading: Bool = false
    @Published var isConnected: Bool = false
    @Published var privacyMode: PrivacyMode = .cloudAllowed
    @Published var lastModelUsed: String = ""
    @Published var lastComplexity: String = ""
    @Published var errorMessage: String?

    // MARK: - Private Properties

    private let wsClient: WebSocketClient
    private var currentStreamingMessageId: UUID?

    // MARK: - Initialization

    init() {
        wsClient = WebSocketClient()
        wsClient.delegate = self
    }

    // MARK: - Public Methods

    /// Connect to the backend WebSocket
    func connect() {
        wsClient.connect()
    }

    /// Disconnect from the backend
    func disconnect() {
        wsClient.disconnect()
    }

    /// Send a message to the assistant
    func sendMessage(_ text: String) async {
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return
        }

        // Ensure connected
        if !isConnected {
            wsClient.connect()
            // Brief delay to allow connection
            try? await Task.sleep(nanoseconds: 100_000_000)
        }

        // Add user message
        let userMessage = Message(role: .user, content: text)
        messages.append(userMessage)

        // Prepare streaming state
        isLoading = true
        errorMessage = nil
        currentStreamingContent = ""

        // Create placeholder for assistant response
        let assistantMessageId = UUID()
        currentStreamingMessageId = assistantMessageId
        let assistantMessage = Message(
            id: assistantMessageId,
            role: .assistant,
            content: "",
            isStreaming: true
        )
        messages.append(assistantMessage)

        // Send to backend
        wsClient.send(message: text, privacyMode: privacyMode.rawValue)
    }

    /// Clear conversation history
    func clearHistory() {
        messages.removeAll()
        currentStreamingContent = ""
        currentStreamingMessageId = nil
        errorMessage = nil
    }

    // MARK: - WebSocketClientDelegate

    func webSocketDidConnect() {
        isConnected = true
    }

    func webSocketDidDisconnect() {
        isConnected = false
    }

    func webSocketDidFail(error: Error) {
        isConnected = false
        handleError("Connection failed: \(error.localizedDescription)")
    }

    func webSocketDidReceiveModelInfo(model: String, complexity: String, privacyMode: String) {
        lastModelUsed = model
        lastComplexity = complexity
    }

    func webSocketDidReceiveToken(_ token: String) {
        appendToken(token)
    }

    func webSocketDidComplete(model: String, reasoning: String) {
        completeStreaming(model: model)
    }

    func webSocketDidReceiveError(_ message: String) {
        handleError(message)
    }

    // MARK: - Private Methods

    private func appendToken(_ token: String) {
        currentStreamingContent += token

        // Update the streaming message
        if let messageId = currentStreamingMessageId,
           let index = messages.firstIndex(where: { $0.id == messageId }) {
            messages[index].content = currentStreamingContent
        }
    }

    private func completeStreaming(model: String) {
        isLoading = false

        // Finalize the streaming message
        if let messageId = currentStreamingMessageId,
           let index = messages.firstIndex(where: { $0.id == messageId }) {
            messages[index].content = currentStreamingContent
            messages[index].isStreaming = false
            messages[index].modelUsed = model
        }

        currentStreamingMessageId = nil
        currentStreamingContent = ""
        lastModelUsed = model
    }

    private func handleError(_ error: String) {
        isLoading = false
        errorMessage = error

        // Remove streaming message if present
        if let messageId = currentStreamingMessageId {
            messages.removeAll { $0.id == messageId }
        }

        currentStreamingMessageId = nil
        currentStreamingContent = ""
    }
}
