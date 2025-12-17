// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "ResearchTool",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(name: "ResearchTool", targets: ["ResearchTool"])
    ],
    targets: [
        .executableTarget(
            name: "ResearchTool",
            path: "ResearchTool",
            exclude: ["Resources"],
            sources: [
                "App/ResearchToolApp.swift",
                "App/AppState.swift",
                "Models/Message.swift",
                "Services/WebSocketClient.swift",
                "Services/BackendLauncher.swift",
                "Services/APIClient.swift",
                "Services/KeychainService.swift",
                "ViewModels/ChatViewModel.swift",
                "ViewModels/ResearchViewModel.swift",
                "ViewModels/LibraryViewModel.swift",
                "Views/ChatView.swift",
                "Views/MainView.swift",
                "Views/MessageBubble.swift",
                "Views/PrivacyModePicker.swift",
                "Views/SettingsView.swift",
                "Views/ExportView.swift",
                "Views/ResearchView.swift",
                "Views/LibraryView.swift",
                "Views/SessionDetailView.swift"
            ]
        )
    ]
)
