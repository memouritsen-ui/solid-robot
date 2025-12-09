import Foundation

/// Represents a chat message in the conversation
struct Message: Identifiable, Equatable {
    let id: UUID
    let role: Role
    var content: String
    let timestamp: Date
    var modelUsed: String?
    var isStreaming: Bool

    /// Message sender role
    enum Role: String {
        case user
        case assistant
        case system
    }

    init(
        id: UUID = UUID(),
        role: Role,
        content: String,
        timestamp: Date = Date(),
        modelUsed: String? = nil,
        isStreaming: Bool = false
    ) {
        self.id = id
        self.role = role
        self.content = content
        self.timestamp = timestamp
        self.modelUsed = modelUsed
        self.isStreaming = isStreaming
    }
}

/// Privacy mode options matching backend PrivacyMode enum
enum PrivacyMode: String, CaseIterable, Identifiable {
    case localOnly = "local_only"
    case cloudAllowed = "cloud_allowed"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .localOnly:
            return "Local Only"
        case .cloudAllowed:
            return "Cloud Allowed"
        }
    }

    var description: String {
        switch self {
        case .localOnly:
            return "Data stays on device. Uses local models only."
        case .cloudAllowed:
            return "May use cloud APIs for better results."
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
