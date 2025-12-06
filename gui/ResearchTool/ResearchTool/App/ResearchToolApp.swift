import SwiftUI

@main
struct ResearchToolApp: App {
    var body: some Scene {
        WindowGroup {
            NavigationStack {
                ChatView()
            }
        }
        .windowStyle(.automatic)
        .defaultSize(width: 800, height: 600)
    }
}
