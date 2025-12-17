import Foundation
import Security

/// Service for securely storing and retrieving API keys from macOS Keychain
class KeychainService {

    // MARK: - Singleton

    static let shared = KeychainService()

    // MARK: - Constants

    private let serviceName = "com.solidrobot.researchtool"

    /// Supported API key types
    enum APIKeyType: String, CaseIterable {
        case anthropic = "ANTHROPIC_API_KEY"
        case tavily = "TAVILY_API_KEY"
        case brave = "BRAVE_API_KEY"
        case exa = "EXA_API_KEY"

        var displayName: String {
            switch self {
            case .anthropic: return "Anthropic (Claude)"
            case .tavily: return "Tavily Search"
            case .brave: return "Brave Search"
            case .exa: return "Exa Search"
            }
        }

        var placeholder: String {
            switch self {
            case .anthropic: return "sk-ant-..."
            case .tavily: return "tvly-..."
            case .brave: return "BSA..."
            case .exa: return "exa-..."
            }
        }

        var icon: String {
            switch self {
            case .anthropic: return "brain"
            case .tavily: return "magnifyingglass"
            case .brave: return "shield"
            case .exa: return "doc.text.magnifyingglass"
            }
        }
    }

    // MARK: - Initialization

    private init() {}

    // MARK: - Public Methods

    /// Save an API key to Keychain
    /// - Parameters:
    ///   - key: The API key value
    ///   - type: The type of API key
    /// - Returns: True if successful
    @discardableResult
    func saveKey(_ key: String, for type: APIKeyType) -> Bool {
        // Delete existing key first
        deleteKey(for: type)

        guard let data = key.data(using: .utf8) else {
            return false
        }

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: type.rawValue,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        ]

        let status = SecItemAdd(query as CFDictionary, nil)
        return status == errSecSuccess
    }

    /// Retrieve an API key from Keychain
    /// - Parameter type: The type of API key
    /// - Returns: The API key if found
    func getKey(for type: APIKeyType) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: type.rawValue,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let key = String(data: data, encoding: .utf8) else {
            return nil
        }

        return key
    }

    /// Delete an API key from Keychain
    /// - Parameter type: The type of API key
    /// - Returns: True if successful
    @discardableResult
    func deleteKey(for type: APIKeyType) -> Bool {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: type.rawValue
        ]

        let status = SecItemDelete(query as CFDictionary)
        return status == errSecSuccess || status == errSecItemNotFound
    }

    /// Check if a key exists in Keychain
    /// - Parameter type: The type of API key
    /// - Returns: True if key exists
    func hasKey(for type: APIKeyType) -> Bool {
        return getKey(for: type) != nil
    }

    /// Get all configured keys as environment-style dictionary
    /// - Returns: Dictionary of key type to value
    func getAllKeys() -> [String: String] {
        var keys: [String: String] = [:]
        for type in APIKeyType.allCases {
            if let key = getKey(for: type) {
                keys[type.rawValue] = key
            }
        }
        return keys
    }

    /// Delete all API keys
    func deleteAllKeys() {
        for type in APIKeyType.allCases {
            deleteKey(for: type)
        }
    }
}
