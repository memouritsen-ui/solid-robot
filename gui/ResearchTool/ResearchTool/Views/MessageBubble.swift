import SwiftUI

/// Displays a single chat message bubble
struct MessageBubble: View {
    let message: Message

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            if message.role == .user {
                Spacer(minLength: 60)
            }

            VStack(alignment: message.role == .user ? .trailing : .leading, spacing: 4) {
                // Message content
                HStack {
                    if message.role == .assistant {
                        // Assistant avatar
                        Image(systemName: "cpu")
                            .foregroundColor(.blue)
                            .frame(width: 24, height: 24)
                    }

                    Text(message.content.isEmpty && message.isStreaming ? "..." : message.content)
                        .padding(12)
                        .background(bubbleBackground)
                        .foregroundColor(bubbleForeground)
                        .cornerRadius(16)
                        .textSelection(.enabled)

                    if message.role == .user {
                        // User avatar
                        Image(systemName: "person.circle.fill")
                            .foregroundColor(.gray)
                            .frame(width: 24, height: 24)
                    }
                }

                // Metadata row
                HStack(spacing: 8) {
                    if message.isStreaming {
                        ProgressView()
                            .controlSize(.mini)
                    }

                    if let model = message.modelUsed {
                        Text(model)
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }

                    Text(message.timestamp, style: .time)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
                .padding(.horizontal, message.role == .user ? 36 : 36)
            }

            if message.role == .assistant {
                Spacer(minLength: 60)
            }
        }
    }

    private var bubbleBackground: Color {
        switch message.role {
        case .user:
            return .blue
        case .assistant:
            return Color(.controlBackgroundColor)
        case .system:
            return .orange.opacity(0.2)
        }
    }

    private var bubbleForeground: Color {
        switch message.role {
        case .user:
            return .white
        case .assistant, .system:
            return .primary
        }
    }
}

// Preview requires Xcode, not available in Swift Package Manager
// #Preview { ... }
