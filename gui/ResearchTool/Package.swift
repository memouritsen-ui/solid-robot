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
                "Models/Message.swift",
                "Services/WebSocketClient.swift",
                "ViewModels/ChatViewModel.swift",
                "Views/ChatView.swift",
                "Views/MessageBubble.swift",
                "Views/PrivacyModePicker.swift"
            ]
        )
    ]
)
